"""Bank-statement PDF -> CSV converter (digital / text-layer PDFs).

Extracts transaction rows from Chinese bank-statement PDFs and writes a CSV
with columns: 日期, 摘要, 支出, 收入, 余额, 原始行.

Supported layouts (v1):
- Table-based statements (pdfplumber table extraction), with either
  separate 借方/贷方 (支出/收入) columns or a single signed 金额 column.
- Plain-text-line statements (fallback line parser) in the same column
  conventions.
- Date formats: YYYY-MM-DD, YYYY/MM/DD, YYYY年MM月DD日, MM-DD, MM/DD
  (bare month-day dates take their year from the statement year, inferred
  from the document or passed explicitly via --year).
- Amounts with thousands commas, leading + / - signs, and (123.45)
  parenthesised negatives.
- Multi-page statements.

NOT supported in this unit: image-only (scanned) PDFs -- they have no text
layer for pdfplumber to read. See README.md "OCR 状态" for the status of
the scanned-PDF path. Password-protected (encrypted) PDFs are also not
supported: the CLI refuses them with a plain-language error (exit 2) instead
of a traceback, and the GUI reports them as unreadable. No network calls
are made at runtime.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber


class PasswordProtectedError(ValueError):
    """Raised when the input PDF is password-protected (encrypted).

    pdfplumber surfaces this as a PdfminerException with an empty message
    wrapping pdfminer's PDFPasswordIncorrect, which is useless to a user,
    so extract_transactions() translates it into this error with a
    human-readable message.
    """


def _is_password_error(exc: BaseException) -> bool:
    """Walk the exception chain looking for pdfminer's PDFPasswordIncorrect.

    Checked by class name (not import) so the converter keeps pdfplumber as
    its only declared runtime dependency; pdfminer.six ships with it.
    """
    seen: set[int] = set()
    cur: BaseException | None = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if type(cur).__name__ == "PDFPasswordIncorrect":
            return True
        cur = cur.__context__ or cur.__cause__
    return False

CSV_COLUMNS = ["日期", "摘要", "支出", "收入", "余额", "原始行"]

_DATE_FULL = re.compile(
    r"(?P<y>20\d{2})[-/年](?P<m>\d{1,2})[-/月](?P<d>\d{1,2})[日]?"
)
_DATE_MD = re.compile(r"(?P<m>\d{1,2})[-/](?P<d>\d{1,2})(?!\d)")
_YEAR_HINT = re.compile(r"(20\d{2})\s*年")
_AMOUNT = re.compile(r"\(?-?\+?[\d,]+\.\d{1,2}\)?|\(?-?\+?[\d,]+\)?")

# Header keywords (substring match, case-insensitive where applicable).
DATE_KEYS = ("日期", "交易日", "记账日", "发生日")
DESC_KEYS = ("摘要", "对方", "交易说明", "说明", "用途", "对方户名", "交易对方")
DEBIT_KEYS = ("支出", "借方", "借", "付款", "转出")
CREDIT_KEYS = ("收入", "贷方", "贷", "收款", "转入")
BALANCE_KEYS = ("余额", "结余")
AMOUNT_KEYS = ("金额", "交易金额", "发生额")


@dataclass
class Transaction:
    date: str          # normalised YYYY-MM-DD
    description: str
    debit: str = ""    # 支出, plain number with 2 decimals, or ""
    credit: str = ""   # 收入, plain number with 2 decimals, or ""
    balance: str = ""
    raw: str = ""      # 原始行 passthrough

    def as_row(self) -> list[str]:
        return [self.date, self.description, self.debit,
                self.credit, self.balance, self.raw]


def _norm(text: str | None) -> str:
    """Normalise extracted text: NFKC folds compatibility variants that
    some PDF producers emit (non-breaking hyphen U+2011 -> '-', CJK
    compatibility ideographs U+FA08 etc. -> their standard code points,
    full-width digits -> ASCII digits)."""
    if text is None:
        return ""
    return unicodedata.normalize("NFKC", str(text)).strip()


def parse_amount(text: str) -> str:
    """Normalise an amount string to a plain 2-decimal number, keeping sign.

    Returns "" for empty / non-numeric input. Handles thousands commas,
    leading +/- signs and (123.45) parenthesised negatives.
    """
    if text is None:
        return ""
    s = _norm(text).replace(" ", "")
    if not s or s in ("-", "--", "—", "/"):
        return ""
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    if s.startswith("+"):
        s = s[1:]
    elif s.startswith("-"):
        negative = True
        s = s[1:]
    s = s.replace(",", "")
    if not re.fullmatch(r"\d+(\.\d{1,2})?", s):
        return ""
    value = float(s)
    if negative:
        value = -value
    return f"{value:.2f}"


def parse_date(text: str, statement_year: int | None) -> str | None:
    """Parse a date cell to YYYY-MM-DD, or None if not a date."""
    if text is None:
        return None
    s = _norm(text)
    m = _DATE_FULL.search(s)
    if m:
        return f"{int(m.group('y')):04d}-{int(m.group('m')):02d}-{int(m.group('d')):02d}"
    m = _DATE_MD.search(s)
    if m and statement_year:
        return (f"{statement_year:04d}-{int(m.group('m')):02d}-"
                f"{int(m.group('d')):02d}")
    return None


def _col_index(header: list[str], keys: tuple[str, ...]) -> int | None:
    for i, cell in enumerate(header):
        c = (cell or "").strip()
        if c and any(k in c for k in keys):
            return i
    return None


def _classify_header(header: list[str]) -> dict | None:
    """Map header cells to roles; None if this is not a transaction table."""
    date_i = _col_index(header, DATE_KEYS)
    if date_i is None:
        return None
    desc_i = _col_index(header, DESC_KEYS)
    debit_i = _col_index(header, DEBIT_KEYS)
    credit_i = _col_index(header, CREDIT_KEYS)
    amount_i = _col_index(header, AMOUNT_KEYS)
    balance_i = _col_index(header, BALANCE_KEYS)
    # Need a date column plus at least one amount column.
    if debit_i is None and credit_i is None and amount_i is None:
        return None
    return {
        "date": date_i,
        "desc": desc_i,
        "debit": debit_i,
        "credit": credit_i,
        "amount": amount_i,
        "balance": balance_i,
    }


def _rows_from_table(table: list[list[str | None]],
                     statement_year: int | None) -> list[Transaction]:
    txns: list[Transaction] = []
    header_map: dict | None = None
    for row in table:
        cells = [_norm(c) for c in row]
        if not any(cells):
            continue
        if header_map is None:
            header_map = _classify_header(cells)
            continue
        if header_map is None:
            continue
        date = parse_date(cells[header_map["date"]], statement_year)
        if date is None:
            continue  # subtotal / footer / continuation row without a date
        desc = cells[header_map["desc"]] if header_map["desc"] is not None else ""
        debit = credit = ""
        if header_map["amount"] is not None:
            amt = parse_amount(cells[header_map["amount"]])
            if amt:
                if amt.startswith("-"):
                    debit = amt[1:]
                else:
                    credit = amt
        else:
            if header_map["debit"] is not None:
                debit = parse_amount(cells[header_map["debit"]])
            if header_map["credit"] is not None:
                credit = parse_amount(cells[header_map["credit"]])
        balance = ""
        if header_map["balance"] is not None:
            balance = parse_amount(cells[header_map["balance"]])
        raw = " | ".join(c for c in cells if c)
        txns.append(Transaction(date, desc, debit, credit, balance, raw))
    return txns


def _rows_from_text_lines(lines: list[str],
                          statement_year: int | None) -> list[Transaction]:
    """Fallback parser for statements without extractable tables.

    Expected line shape: <date> <description...> <amount> [<amount> ...]
    Trailing numbers are read right-to-left: last = 余额 when there are
    2-3 trailing numbers, the one(s) before it are debit/credit/amount.
    A single signed amount goes to 支出 (negative) or 收入 (positive).
    """
    txns: list[Transaction] = []
    for line in lines:
        s = _norm(line)
        if not s:
            continue
        m = _DATE_FULL.search(s) or _DATE_MD.search(s)
        if not m:
            continue
        date = parse_date(s[: m.end() + 1], statement_year)
        if date is None:
            continue
        rest = s[m.end():].strip()
        amounts = _AMOUNT.findall(rest)
        if not amounts:
            continue
        # Description = rest with the trailing amount tokens removed.
        # Chop the exact matched amount substrings off the end, last first
        # (a regex strip here would also eat the ".00" of the amount before
        # it, because a bare-integer pattern matches the decimal tail).
        desc = rest
        for amt in reversed(amounts):
            tail = desc.rstrip()
            if tail.endswith(amt):
                desc = tail[:-len(amt)].rstrip()
        parsed = [parse_amount(a) for a in amounts]
        parsed = [p for p in parsed if p]
        debit = credit = balance = ""
        if len(parsed) == 1:
            if parsed[0].startswith("-"):
                debit = parsed[0][1:]
            else:
                credit = parsed[0]
        elif len(parsed) == 2:
            amt, balance = parsed
            if amt.startswith("-"):
                debit = amt[1:]
            else:
                credit = amt
        elif len(parsed) >= 3:
            debit, credit, balance = parsed[0], parsed[1], parsed[2]
            debit = debit.lstrip("-") if debit.startswith("-") else debit
        txns.append(Transaction(date, desc, debit, credit, balance, s))
    return txns


def infer_statement_year(pages_text: list[str]) -> int | None:
    """Infer the statement year from a 'YYYY年' hint or the first full date."""
    for text in pages_text:
        m = _YEAR_HINT.search(text or "")
        if m:
            return int(m.group(1))
    for text in pages_text:
        m = _DATE_FULL.search(text or "")
        if m:
            return int(m.group("y"))
    return None


def extract_transactions(pdf_path: str | Path,
                         statement_year: int | None = None
                         ) -> list[Transaction]:
    """Extract all transactions from a text-layer bank-statement PDF.

    Raises PasswordProtectedError for password-protected (encrypted) PDFs.
    """
    txns: list[Transaction] = []
    pages_text: list[str] = []
    try:
        pdf = pdfplumber.open(str(pdf_path))
    except Exception as exc:
        if _is_password_error(exc):
            raise PasswordProtectedError(
                "this PDF is password-protected (encrypted). "
                "Decrypt it first (e.g. open it in a PDF reader and save "
                "an unprotected copy), then convert."
            ) from exc
        raise
    with pdf:
        pages = list(pdf.pages)
        for page in pages:
            pages_text.append(page.extract_text() or "")
        year = statement_year or infer_statement_year(pages_text)
        for i, page in enumerate(pages):
            tables = page.extract_tables() or []
            page_txns: list[Transaction] = []
            for table in tables:
                page_txns.extend(_rows_from_table(table, year))
            if not page_txns:
                # No usable table on this page: fall back to line parsing.
                lines = (pages_text[i] or "").splitlines()
                page_txns = _rows_from_text_lines(lines, year)
            txns.extend(page_txns)
    return txns


def write_csv(transactions: list[Transaction], out_path: str | Path) -> None:
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        for t in transactions:
            writer.writerow(t.as_row())


def convert(pdf_path: str | Path, csv_path: str | Path,
             statement_year: int | None = None) -> list[Transaction]:
    txns = extract_transactions(pdf_path, statement_year)
    write_csv(txns, csv_path)
    return txns


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Convert a text-layer bank-statement PDF to CSV.")
    ap.add_argument("pdf", help="input bank-statement PDF")
    ap.add_argument("csv", nargs="?", help="output CSV (default: <pdf>.csv)")
    ap.add_argument("--year", type=int, default=None,
                    help="statement year for MM-DD dates (auto-detected "
                         "from the document when omitted)")
    args = ap.parse_args(argv)
    out = args.csv or str(Path(args.pdf).with_suffix(".csv"))
    try:
        txns = convert(args.pdf, out, args.year)
    except PasswordProtectedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"extracted {len(txns)} transactions -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
