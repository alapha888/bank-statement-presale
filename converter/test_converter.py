"""Validate the converter against synthetic fixtures with ground truth.

Run from converter/:  .venv/bin/python -m pytest test_converter.py -v
or:                    .venv/bin/python validate.py

Compares every extracted field (date, desc, debit, credit, balance) with
ground_truth.json and prints per-fixture row accuracy. Exits non-zero if
any fixture is below 100% row accuracy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bank_statement import extract_transactions, parse_date  # noqa: E402

FIXTURES = HERE / "fixtures"


def compare(pdf_name: str) -> dict:
    truth = json.loads((FIXTURES / "ground_truth.json").read_text(encoding="utf-8"))[pdf_name]
    got = extract_transactions(FIXTURES / pdf_name)
    errors: list[str] = []
    n_correct = 0
    for i, t in enumerate(truth):
        if i >= len(got):
            errors.append(f"row {i+1}: missing (expected {t})")
            continue
        g = got[i]
        field_errors = []
        want_date = parse_date(t["date"], 2026) or t["date"]
        if g.date != want_date:
            field_errors.append(f"date got {g.date!r} want {want_date!r}")
        if g.description != t["desc"]:
            field_errors.append(f"desc got {g.description!r} want {t['desc']!r}")
        if (g.debit or "") != (t["debit"] or ""):
            field_errors.append(f"debit got {g.debit!r} want {t['debit']!r}")
        if (g.credit or "") != (t["credit"] or ""):
            field_errors.append(f"credit got {g.credit!r} want {t['credit']!r}")
        if (g.balance or "") != (t["balance"] or ""):
            field_errors.append(f"balance got {g.balance!r} want {t['balance']!r}")
        if field_errors:
            errors.append(f"row {i+1} ({t['date']} {t['desc']}): " + "; ".join(field_errors))
        else:
            n_correct += 1
    if len(got) > len(truth):
        for g in got[len(truth):]:
            errors.append(f"extra row: {g.date} {g.description} {g.debit} {g.credit}")
    return {
        "file": pdf_name,
        "total": len(truth),
        "extracted": len(got),
        "correct": n_correct,
        "accuracy": n_correct / len(truth) if truth else 0.0,
        "errors": errors,
    }


def main() -> int:
    results = []
    for name in _pdf_names():
        r = compare(name)
        results.append(r)
        status = "PASS" if r["accuracy"] == 1.0 and not r["errors"] else "FAIL"
        print(f"[{status}] {r['file']}: {r['correct']}/{r['total']} rows "
              f"correct ({r['accuracy']:.0%}), extracted {r['extracted']}")
        for e in r["errors"]:
            print(f"    - {e}")
    all_pass = all(r["accuracy"] == 1.0 and not r["errors"] for r in results)
    print(f"\nTOTAL: {sum(r['correct'] for r in results)}/"
          f"{sum(r['total'] for r in results)} rows correct")
    return 0 if all_pass else 1


# ---- pytest entry points -------------------------------------------------
def _pdf_names():
    # Exactly the fixtures with ground truth in ground_truth.json (A-D).
    # The scanned fixture is covered separately by test_ocr.py and has no
    # ground-truth entry of its own (its truth is fixture D's, under
    # "fixture-d-text-lines.pdf"); the E* edge fixtures are covered by
    # test_edge_cases.py against ground_truth_edge.json.
    truth = json.loads((FIXTURES / "ground_truth.json").read_text(
        encoding="utf-8"))
    return sorted(truth)


def test_fixtures():
    for name in _pdf_names():
        r = compare(name)
        assert r["accuracy"] == 1.0, f"{name}: {r['errors']}"
        assert not r["errors"], f"{name}: {r['errors']}"


def test_parse_date_rejects_impossible_dates():
    """Real-sample finding (2026-11-07): the line parser matches any NN/NN
    fragment, so a sort-code-like fragment or a DD/MM date used to pass
    through as an impossible month/day (e.g. 2023-60-83, 2023-31-10).
    parse_date must reject those instead of returning garbage."""
    assert parse_date("60-83-71", 2023) is None
    assert parse_date("31/10", 2023) is None  # DD/MM, not MM/DD
    assert parse_date("2023-13-40", None) is None
    assert parse_date("2023-02-30", None) is None
    # Valid dates are unchanged.
    assert parse_date("2023-10-03", None) == "2023-10-03"
    assert parse_date("03/10", 2023) == "2023-03-10"
    assert parse_date("2023/10/03", None) == "2023-10-03"


if __name__ == "__main__":
    sys.exit(main())
