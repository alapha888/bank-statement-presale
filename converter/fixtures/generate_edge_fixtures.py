"""Generate edge-case fixtures for the bank-statement converter.

Run AFTER fixtures/generate_fixtures.py (E1 re-encrypts fixture A):
  .venv/bin/python fixtures/generate_edge_fixtures.py

Outputs fixtures/fixture-e*.pdf and fixtures/ground_truth_edge.json.

E1 fixture-e1-encrypted.pdf -- fixture A re-saved with AES-256 encryption
   (user password "test123", documented here and in test_edge_cases.py).
   Expected: the converter refuses it with PasswordProtectedError; the CLI
   exits 2 with a plain-language message and writes no CSV.
E2 fixture-e2-mixed-image.pdf -- fixture A content (same 12 rows, 2 pages)
   plus an embedded raster stamp image ("业务专用章") on page 1. The text
   layer is untouched. Expected: extraction identical to fixture A, 12/12.
E3 fixture-e3-no-ruling-lines.pdf -- the same 12 rows, same column x
   positions, but NO table ruling lines at all, so pdfplumber finds no
   table and the line-parser fallback runs. Amounts here are unsigned
   (separate debit/credit columns, no +/- sign), so the fallback cannot
   tell a debit from a credit: it assigns any single amount to 收入.
   Expected (characterisation, see test_edge_cases.py): 12/12 rows found,
   12/12 dates right, but only the 2 credit rows are fully correct; the
   10 debit rows come back with debit/credit swapped. This is a real,
   documented limitation, not a pass: fixing it needs column positions
   (e.g. pdfplumber extract_words x-coordinates) in the fallback, which
   is out of scope for presale v1.

All payee names / amounts are invented, same as the A-D fixtures.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from generate_fixtures import (  # noqa: E402
    FS_CELL,
    MARGIN,
    ROW_H,
    build_rows,
    money,
    new_statement,
    put_text,
)

SPEC_A = [
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
WIDTHS_A = [90, 190, 75, 75, 85]
HEADER_A = ["交易日期", "摘要", "借方(支出)", "贷方(收入)", "余额"]
E1_USER_PASSWORD = "test123"


def _table_rows(rows):
    return [[r["date"], r["desc"],
             money(float(r["debit"])) if r["debit"] else "",
             money(float(r["credit"])) if r["credit"] else "",
             money(float(r["balance"]))] for r in rows]


def _stamp_png() -> bytes:
    """Render a small red 'business stamp' image with PyMuPDF only."""
    doc = pymupdf.open()
    page = doc.new_page(width=160, height=80)
    page.draw_rect(pymupdf.Rect(4, 4, 156, 76), color=(0.8, 0, 0), width=3)
    page.insert_text((18, 34), "某某银行", fontsize=16,
                     fontname="china-s", color=(0.8, 0, 0))
    page.insert_text((18, 60), "业务专用章", fontsize=16,
                     fontname="china-s", color=(0.8, 0, 0))
    png = page.get_pixmap(dpi=150).tobytes("png")
    doc.close()
    return png


def _draw_text_only_table(page, y0, widths, header, rows):
    """Draw header + rows as positioned text only -- no ruling lines."""
    xs = [MARGIN]
    for w in widths:
        xs.append(xs[-1] + w)
    for j, h in enumerate(header):
        put_text(page, (xs[j] + 4, y0 + 15), h, FS_CELL)
    for i, row in enumerate(rows):
        y = y0 + (i + 1) * ROW_H + 15
        for j, cell in enumerate(row):
            if cell:
                put_text(page, (xs[j] + 4, y), cell, FS_CELL)


def main() -> None:
    rows_a = build_rows(SPEC_A, opening=10000.00)
    truth_rows = [
        {"date": r["date"], "desc": r["desc"], "debit": r["debit"],
         "credit": r["credit"], "balance": r["balance"]} for r in rows_a
    ]
    truth: dict[str, list[dict]] = {}

    # ---- E1: encrypted copy of fixture A.
    src = pymupdf.open(HERE / "fixture-a-two-col-two-page.pdf")
    src.save(HERE / "fixture-e1-encrypted.pdf",
             encryption=pymupdf.PDF_ENCRYPT_AES_256,
             user_pw=E1_USER_PASSWORD, owner_pw="owner-test-only")
    src.close()

    # ---- E2: fixture A content + embedded raster stamp image, page 1.
    from generate_fixtures import draw_table  # noqa: E402
    doc_e2, page_e2 = new_statement("某某银行 个人活期账户交易明细 2026年1月")
    table_rows = _table_rows(rows_a)
    draw_table(page_e2, MARGIN, 90, WIDTHS_A, HEADER_A, table_rows[:6])
    page_e2.insert_image(pymupdf.Rect(470, 28, 550, 68),
                         stream=_stamp_png())
    page_e2b = doc_e2.new_page(width=595, height=842)
    put_text(page_e2b, (MARGIN, 60),
             "某某银行 个人活期账户交易明细 2026年1月(续)", 14)
    draw_table(page_e2b, MARGIN, 90, WIDTHS_A, HEADER_A, table_rows[6:])
    doc_e2.save(HERE / "fixture-e2-mixed-image.pdf")
    truth["fixture-e2-mixed-image.pdf"] = truth_rows

    # ---- E3: same rows, no ruling lines (line-parser fallback).
    doc_e3, page_e3 = new_statement("某某银行 个人活期账户交易明细 2026年1月")
    _draw_text_only_table(page_e3, 90, WIDTHS_A, HEADER_A, table_rows[:6])
    page_e3b = doc_e3.new_page(width=595, height=842)
    put_text(page_e3b, (MARGIN, 60),
             "某某银行 个人活期账户交易明细 2026年1月(续)", 14)
    _draw_text_only_table(page_e3b, 90, WIDTHS_A, HEADER_A, table_rows[6:])
    doc_e3.save(HERE / "fixture-e3-no-ruling-lines.pdf")
    truth["fixture-e3-no-ruling-lines.pdf"] = truth_rows

    (HERE / "ground_truth_edge.json").write_text(
        json.dumps(truth, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote 3 edge fixtures (E1 encrypted, E2 mixed image, "
          "E3 no ruling lines), 12 ground-truth rows each for E2/E3")


if __name__ == "__main__":
    main()
