"""Generate synthetic Chinese bank-statement PDF fixtures + ground truth.

Run:  .venv/bin/python fixtures/generate_fixtures.py
Outputs fixtures/*.pdf and fixtures/ground_truth.json.

Built with PyMuPDF using its built-in CJK font ("china-s") so the text
layer extracts cleanly. (An earlier reportlab build used a .ttc font whose
ToUnicode map extracted every CJK glyph as \\x00; see README.md.)

All payee names / amounts are invented. Balances are a running total from
the stated opening balance, so ground truth is internally consistent.
Fixtures A-C are grid tables (exercises pdfplumber table extraction);
fixture D is plain text lines (exercises the line-parser fallback).
"""

from __future__ import annotations

import json
from pathlib import Path

import pymupdf  # PyMuPDF; fixtures only, NOT a converter runtime dependency

HERE = Path(__file__).resolve().parent
# Text rendering: mixed fonts, because no single embedded CJK font in this
# VM extracts cleanly through pdfplumber:
# - reportlab + NotoSansCJK .ttc -> every CJK glyph extracts as \\x00
#   (broken ToUnicode map).
# - PyMuPDF + NotoSansCJK (any face incl. extracted SC) -> hyphen-minus
#   extracts as U+2011 and some CJK chars as compatibility ideographs
#   (e.g. U+FA08 for \u884c).
# - PyMuPDF built-in "china-s" extracts CJK to standard code points, but
#   renders ASCII digits full-width, overflowing narrow numeric columns.
# So CJK runs use "china-s" and ASCII runs use Helvetica, positioned with
# measured advances. (Fixtures only; the converter itself only reads PDFs.)
import pymupdf as _pymupdf

_F_CJK = _pymupdf.Font("china-s")
_F_ASC = _pymupdf.Font("helv")
FS_TITLE = 14
FS_CELL = 11
MARGIN = 40
ROW_H = 22


def put_text(page, point, text, fontsize):
    """Insert text, splitting CJK runs (china-s) from ASCII runs (helv)."""
    x, y = point
    runs: list[tuple[str, bool]] = []
    cur, cur_cjk = "", None
    for ch in text:
        cjk = ord(ch) > 0x7E
        if cur_cjk is None or cjk == cur_cjk:
            cur += ch
            cur_cjk = cjk
        else:
            runs.append((cur, cur_cjk))
            cur, cur_cjk = ch, cjk
    if cur:
        runs.append((cur, cur_cjk))
    for run, cjk in runs:
        font = _F_CJK if cjk else _F_ASC
        page.insert_text((x, y), run, fontsize=fontsize,
                         fontname="china-s" if cjk else "helv")
        x += font.text_length(run, fontsize=fontsize)


def money(v: float) -> str:
    return f"{v:,.2f}"


def build_rows(spec: list[tuple[str, str, float, float]], opening: float):
    """spec: (date, desc, debit, credit). Returns rows with running balance."""
    bal = opening
    rows = []
    for date, desc, debit, credit in spec:
        bal = bal - debit + credit
        rows.append({
            "date": date, "desc": desc,
            "debit": f"{debit:.2f}" if debit else "",
            "credit": f"{credit:.2f}" if credit else "",
            "balance": f"{bal:.2f}",
        })
    return rows


def draw_table(page: pymupdf.Page, x0: float, y0: float,
               widths: list[float], header: list[str],
               rows: list[list[str]]) -> None:
    """Draw a grid table with explicit ruling lines + text per cell."""
    ncols = len(widths)
    xs = [x0]
    for w in widths:
        xs.append(xs[-1] + w)
    total_h = ROW_H * (len(rows) + 1)
    # Horizontal lines (header bottom doubled visually by a filled rect).
    # Header shading, then grid lines.
    page.draw_rect(pymupdf.Rect(x0, y0, xs[-1], y0 + ROW_H),
                   fill=(0.85, 0.85, 0.85), color=(0.4, 0.4, 0.4), width=0.5)
    for r in range(len(rows) + 2):
        y = y0 + r * ROW_H
        page.draw_line((x0, y), (xs[-1], y), color=(0.4, 0.4, 0.4), width=0.5)
    for x in xs:
        page.draw_line((x, y0), (x, y0 + total_h), color=(0.4, 0.4, 0.4), width=0.5)
    # Header text.
    for j, h in enumerate(header):
        put_text(page, (xs[j] + 4, y0 + 15), h, FS_CELL)
    # Body text.
    for i, row in enumerate(rows):
        y = y0 + (i + 1) * ROW_H + 15
        for j, cell in enumerate(row):
            if cell:
                put_text(page, (xs[j] + 4, y), cell, FS_CELL)


def new_statement(title: str) -> tuple[pymupdf.Document, pymupdf.Page]:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4
    put_text(page, (MARGIN, 60), title, FS_TITLE)
    return doc, page


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    truth: dict[str, list[dict]] = {}

    # ---- Fixture A: separate 借方/贷方, YYYY-MM-DD, 2 pages (6 rows each).
    spec_a = [
        ("2026-01-03", "工资-某某科技有限公司", 0, 12500.00),
        ("2026-01-05", "支付宝-淘宝购物", 328.50, 0),
        ("2026-01-06", "微信支付-美团外卖", 46.80, 0),
        ("2026-01-08", "水电费-国网电费代扣", 212.30, 0),
        ("2026-01-10", "财付通-京东购物", 899.00, 0),
        ("2026-01-12", "中国移动-话费充值", 100.00, 0),
        ("2026-01-15", "支付宝-超市购物", 156.20, 0),
        ("2026-01-18", "微信支付-滴滴出行", 38.60, 0),
        ("2026-01-20", "房租-房东张某某", 2800.00, 0),
        ("2026-01-22", "支付宝-基金赎回入账", 0, 5000.00),
        ("2026-01-25", "微信支付-餐饮消费", 128.00, 0),
        ("2026-01-28", "财付通-视频会员续费", 25.00, 0),
    ]
    rows_a = build_rows(spec_a, opening=10000.00)
    widths_a = [90, 190, 75, 75, 85]
    header_a = ["交易日期", "摘要", "借方(支出)", "贷方(收入)", "余额"]
    doc_a, page_a = new_statement("某某银行 个人活期账户交易明细 2026年1月")
    table_rows_a = [[r["date"], r["desc"],
                     money(float(r["debit"])) if r["debit"] else "",
                     money(float(r["credit"])) if r["credit"] else "",
                     money(float(r["balance"]))] for r in rows_a]
    draw_table(page_a, MARGIN, 90, widths_a, header_a, table_rows_a[:6])
    page_a2 = doc_a.new_page(width=595, height=842)
    put_text(page_a2, (MARGIN, 60), "某某银行 个人活期账户交易明细 2026年1月(续)", FS_TITLE)
    draw_table(page_a2, MARGIN, 90, widths_a, header_a, table_rows_a[6:])
    doc_a.save(HERE / "fixture-a-two-col-two-page.pdf")
    truth["fixture-a-two-col-two-page.pdf"] = [
        {"date": r["date"], "desc": r["desc"], "debit": r["debit"],
         "credit": r["credit"], "balance": r["balance"]} for r in rows_a]

    # ---- Fixture B: single signed 金额 column, YYYY/MM/DD.
    spec_b = [
        ("2026/02/02", "工资-某某科技有限公司", 0, 12500.00),
        ("2026/02/04", "支付宝-淘宝购物", 512.40, 0),
        ("2026/02/07", "微信支付-美团外卖", 62.00, 0),
        ("2026/02/09", "水电费-自来水代扣", 88.60, 0),
        ("2026/02/11", "财付通-拼多多购物", 199.90, 0),
        ("2026/02/14", "微信支付-电影票", 79.00, 0),
        ("2026/02/16", "支付宝-理财收益入账", 0, 342.18),
        ("2026/02/20", "中国移动-宽带费", 129.00, 0),
    ]
    rows_b = build_rows(spec_b, opening=8000.00)
    table_rows_b = []
    for r in rows_b:
        amt = ("-" + money(float(r["debit"]))) if r["debit"] else ("+" + money(float(r["credit"])))
        table_rows_b.append([r["date"], r["desc"], amt, money(float(r["balance"]))])
    doc_b, page_b = new_statement("某某银行 借记卡交易明细 2026年2月")
    draw_table(page_b, MARGIN, 90, [90, 220, 100, 105],
               ["日期", "对方户名", "金额", "余额"], table_rows_b)
    doc_b.save(HERE / "fixture-b-single-amount.pdf")
    truth["fixture-b-single-amount.pdf"] = [
        {"date": "2026-02-02" if False else r["date"].replace("/", "-"),
         "desc": r["desc"], "debit": r["debit"],
         "credit": r["credit"], "balance": r["balance"]} for r in rows_b]

    # ---- Fixture C: MM-DD dates (year in title), different column order.
    spec_c = [
        ("03-02", "工资-某某科技有限公司", 0, 12500.00),
        ("03-05", "支付宝-淘宝购物", 1024.75, 0),
        ("03-07", "微信支付-美团外卖", 54.30, 0),
        ("03-10", "水电费-燃气费代扣", 156.00, 0),
        ("03-12", "财付通-京东购物", 459.00, 0),
        ("03-15", "支付宝-超市购物", 231.80, 0),
        ("03-18", "微信支付-高铁票", 248.50, 0),
        ("03-21", "房租-房东张某某", 2800.00, 0),
    ]
    rows_c = build_rows(spec_c, opening=15000.00)
    table_rows_c = [[r["desc"], r["date"],
                     money(float(r["credit"])) if r["credit"] else "",
                     money(float(r["debit"])) if r["debit"] else "",
                     money(float(r["balance"]))] for r in rows_c]
    doc_c, page_c = new_statement("某某银行 个人账户明细 2026年3月")
    draw_table(page_c, MARGIN, 90, [190, 70, 80, 80, 95],
               ["摘要", "交易日期", "收入", "支出", "余额"], table_rows_c)
    doc_c.save(HERE / "fixture-c-mmdd-reordered.pdf")
    truth["fixture-c-mmdd-reordered.pdf"] = [
        {"date": "2026-" + r["date"], "desc": r["desc"], "debit": r["debit"],
         "credit": r["credit"], "balance": r["balance"]} for r in rows_c]

    # ---- Fixture D: plain text lines, no table (fallback parser).
    spec_d = [
        ("2026-04-01", "工资-某某科技有限公司", 0, 12500.00),
        ("2026-04-03", "支付宝-淘宝购物", 289.90, 0),
        ("2026-04-06", "微信支付-美团外卖", 41.20, 0),
        ("2026-04-09", "水电费-电费代扣", 198.45, 0),
        ("2026-04-12", "财付通-京东购物", 679.00, 0),
        ("2026-04-15", "支付宝-理财收益入账", 0, 128.66),
    ]
    rows_d = build_rows(spec_d, opening=9000.00)
    doc_d, page_d = new_statement("某某银行 个人活期账户交易明细 2026年4月")
    y = 110
    for r in rows_d:
        amt = ("-" + money(float(r["debit"]))) if r["debit"] else ("+" + money(float(r["credit"])))
        line = f"{r['date']}  {r['desc']}  {amt}  {money(float(r['balance']))}"
        put_text(page_d, (MARGIN, y), line, FS_CELL)
        y += 22
    doc_d.save(HERE / "fixture-d-text-lines.pdf")
    truth["fixture-d-text-lines.pdf"] = [
        {"date": r["date"], "desc": r["desc"], "debit": r["debit"],
         "credit": r["credit"], "balance": r["balance"]} for r in rows_d]

    (HERE / "ground_truth.json").write_text(
        json.dumps(truth, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(v) for v in truth.values())
    print(f"wrote {len(truth)} fixtures, {total} ground-truth rows")


if __name__ == "__main__":
    main()
