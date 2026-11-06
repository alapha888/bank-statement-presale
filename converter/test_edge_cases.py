"""Edge-case validation: encrypted / mixed-image / no-ruling-lines PDFs.

Run from converter/:  .venv/bin/python -m pytest test_edge_cases.py -v
Requires fixtures/generate_edge_fixtures.py to have run (run_tests.sh does
both generators). Ground truth lives in fixtures/ground_truth_edge.json;
E2/E3 share fixture A's 12 rows.

E1 (encrypted): the converter must refuse with PasswordProtectedError and
the CLI must exit 2 with a plain-language message and write no CSV.
E2 (mixed image): extraction must be identical to fixture A, 12/12 rows.
E3 (no ruling lines): CHARACTERISATION test of a known limitation. Without
ruling lines pdfplumber finds no table, the line-parser fallback runs, and
unsigned amounts in separate debit/credit columns cannot be told apart:
debit rows come back with debit/credit swapped. The test locks in the
measured behaviour (12/12 rows, 12/12 dates, only the 2 credit rows fully
correct) so a future fix -- e.g. using extract_words x-coordinates in the
fallback -- must update this test deliberately, not silently.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bank_statement import (  # noqa: E402
    PasswordProtectedError,
    extract_transactions,
    main,
    parse_date,
)

FIXTURES = HERE / "fixtures"
EDGE_TRUTH = json.loads(
    (FIXTURES / "ground_truth_edge.json").read_text(encoding="utf-8"))
A_TRUTH = json.loads(
    (FIXTURES / "ground_truth.json").read_text(encoding="utf-8")
)["fixture-a-two-col-two-page.pdf"]


def _field_errors(got, want):
    errs = []
    want_date = parse_date(want["date"], 2026) or want["date"]
    if got.date != want_date:
        errs.append(f"date got {got.date!r} want {want_date!r}")
    if got.description != want["desc"]:
        errs.append(f"desc got {got.description!r} want {want['desc']!r}")
    if (got.debit or "") != (want["debit"] or ""):
        errs.append(f"debit got {got.debit!r} want {want['debit']!r}")
    if (got.credit or "") != (want["credit"] or ""):
        errs.append(f"credit got {got.credit!r} want {want['credit']!r}")
    if (got.balance or "") != (want["balance"] or ""):
        errs.append(f"balance got {got.balance!r} want {want['balance']!r}")
    return errs


def test_e1_encrypted_raises_password_error():
    with pytest.raises(PasswordProtectedError) as excinfo:
        extract_transactions(FIXTURES / "fixture-e1-encrypted.pdf")
    assert "password-protected" in str(excinfo.value)


def test_e1_cli_exits_2_with_plain_message_and_no_csv(tmp_path, capsys):
    out = tmp_path / "e1.csv"
    rc = main([str(FIXTURES / "fixture-e1-encrypted.pdf"), str(out)])
    assert rc == 2
    assert not out.exists()
    err = capsys.readouterr().err
    assert "password-protected" in err
    assert "Traceback" not in err


def test_e2_mixed_image_matches_fixture_a():
    got = extract_transactions(FIXTURES / "fixture-e2-mixed-image.pdf")
    truth = EDGE_TRUTH["fixture-e2-mixed-image.pdf"]
    assert truth == A_TRUTH  # generator contract: E2 reuses A's rows
    assert len(got) == 12
    errors = []
    for i, want in enumerate(truth):
        errors.extend(f"row {i+1}: " + e
                      for e in _field_errors(got[i], want))
    assert not errors, "\n".join(errors)


def test_e3_no_ruling_lines_characterisation():
    """Known limitation, locked in: rows + dates survive, debit/credit
    do not. See module docstring; a fallback fix must update this test."""
    got = extract_transactions(FIXTURES / "fixture-e3-no-ruling-lines.pdf")
    truth = EDGE_TRUTH["fixture-e3-no-ruling-lines.pdf"]
    assert len(got) == 12
    # All 12 dates correct.
    for i, want in enumerate(truth):
        want_date = parse_date(want["date"], 2026) or want["date"]
        assert got[i].date == want_date, f"row {i+1} date"
    # Only the 2 credit rows are fully correct; the 10 debit rows have
    # debit/credit swapped (unsigned amounts, no column info in fallback).
    n_fully_correct = sum(
        1 for i, want in enumerate(truth)
        if not _field_errors(got[i], want))
    assert n_fully_correct == 2
    n_swapped = sum(
        1 for i, want in enumerate(truth)
        if want["debit"] and got[i].credit == want["debit"]
        and not got[i].debit)
    assert n_swapped == 10
