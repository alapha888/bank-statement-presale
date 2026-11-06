"""GUI 后端函数测试（不需要显示器）。

Run from converter/:
    .venv/bin/python -m pytest test_gui.py -v
或： ./run_tests.sh

只测 gui.py 里与界面分离的后端：run_conversion / default_output_path。
界面本身（tkinter widgets）不在此测——需要显示器，留给人工点检。
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bank_statement import CSV_COLUMNS  # noqa: E402
from gui import default_output_path, run_conversion  # noqa: E402

FIXTURES = HERE / "fixtures"
FIXTURE_A = FIXTURES / "fixture-a-two-col-two-page.pdf"


def test_fixture_a_csv_has_header_plus_12_rows(tmp_path):
    """fixture A：CSV 应为表头 + 12 行 = 13 行，与 ground truth 一致。"""
    out = tmp_path / "a.csv"
    result = run_conversion(FIXTURE_A, out)
    assert result.ok, f"unexpected error: {result.error}"
    assert result.rows == 12
    assert result.output == str(out)
    assert out.exists()

    with open(out, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    assert len(rows) == 13, f"expected 13 lines (header + 12), got {len(rows)}"
    assert rows[0] == CSV_COLUMNS

    truth = json.loads(
        (FIXTURES / "ground_truth.json").read_text(encoding="utf-8")
    )["fixture-a-two-col-two-page.pdf"]
    for i, t in enumerate(truth):
        got = rows[i + 1]
        assert got[0] == t["date"], f"row {i+1} date: {got[0]!r} != {t['date']!r}"
        assert got[1] == t["desc"], f"row {i+1} desc: {got[1]!r} != {t['desc']!r}"
        assert got[2] == t["debit"]
        assert got[3] == t["credit"]
        assert got[4] == t["balance"]
    # fixture A 是干净表格：疑似漏提应为 0
    assert result.skipped == 0


def test_missing_file_handled_gracefully(tmp_path):
    """不存在的文件：返回失败结果，不抛异常，不生成 CSV。"""
    out = tmp_path / "out.csv"
    result = run_conversion(tmp_path / "不存在.pdf", out)
    assert not result.ok
    assert result.error, "error message must not be empty"
    assert "找不到" in result.error
    assert not out.exists()


def test_non_pdf_input_handled_gracefully(tmp_path):
    """非 PDF 输入：返回失败结果，不抛异常，不生成 CSV。"""
    fake = tmp_path / "not-a-pdf.txt"
    fake.write_text("这不是 PDF\n", encoding="utf-8")
    out = tmp_path / "out.csv"
    result = run_conversion(fake, out)
    assert not result.ok
    assert result.error
    assert "PDF" in result.error
    assert not out.exists()


def test_year_passthrough(tmp_path):
    """year 参数透传给转换逻辑（fixture C 的 MM-DD 日期需年份推断）。"""
    out = tmp_path / "c.csv"
    result = run_conversion(FIXTURES / "fixture-c-mmdd-reordered.pdf", out,
                            year=2026)
    assert result.ok, f"unexpected error: {result.error}"
    assert result.rows == 8
    with open(out, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    assert rows[1][0] == "2026-03-02"


def test_default_output_path():
    """默认输出：与输入同目录、同名 .csv。"""
    assert default_output_path("/tmp/对账单.pdf") == "/tmp/对账单.csv"
    assert default_output_path(Path("x/y/z.PDF")) == str(Path("x/y/z.csv"))
