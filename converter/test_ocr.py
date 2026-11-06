"""End-to-end OCR check for the scanned-PDF path (standalone, not pytest).

Requires the `tesseract` binary with chi_sim data installed on the machine
(`sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim` on Debian/Ubuntu).
Exits 2 with an explanation when tesseract is unavailable -- that means
"OCR not validated here", not a test failure.

Pipeline tested: scanned fixture (image-only PDF, rendered from fixture D)
-> tesseract chi_sim+eng -> bank_statement line parser -> compare with
ground truth. This exercises OCR text quality + the parser; it does NOT
test ocrmypdf (not installed) or any future OCRmyPDF-first pipeline.

Run:  .venv/bin/python test_ocr.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bank_statement import _rows_from_text_lines  # noqa: E402

FIXTURES = HERE / "fixtures"


def main() -> int:
    # The OCR output contains Chinese text. On Windows the console stdout
    # defaults to cp1252, which cannot encode it (observed in CI:
    # UnicodeEncodeError printing the raw OCR text). Force UTF-8 output;
    # on Linux/macOS this is already the default and changes nothing.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    tess = shutil.which("tesseract")
    if tess is None:
        print("tesseract binary NOT FOUND on this machine.")
        print("OCR path NOT VALIDATED. To validate: install tesseract with "
              "Simplified Chinese data, e.g.:")
        print("  sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim")
        print("then re-run: .venv/bin/python test_ocr.py")
        return 2
    png = FIXTURES / "fixture-s1-scanned.png"
    if not png.exists():
        print("scanned fixture missing; run:")
        print("  .venv/bin/python fixtures/make_scanned_fixture.py")
        return 2
    # NOTE: encoding must be explicit. On Windows, text=True alone decodes
    # with the locale encoding (cp1252), which cannot decode tesseract's
    # UTF-8 Chinese output and leaves proc.stdout as None (observed in CI:
    # UnicodeDecodeError byte 0x90 -> AttributeError on splitlines).
    # utf-8-sig also strips a leading BOM if tesseract ever emits one.
    proc = subprocess.run(
        [tess, str(png), "stdout", "-l", "chi_sim+eng", "--psm", "6"],
        capture_output=True, text=True, encoding="utf-8-sig",
        errors="replace")
    ocr_text = proc.stdout
    print("--- OCR raw text ---")
    print(ocr_text)
    print("--------------------")
    truth = json.loads((FIXTURES / "ground_truth.json").read_text(encoding="utf-8"))[
        "fixture-d-text-lines.pdf"]
    got = _rows_from_text_lines(ocr_text.splitlines(), 2026)
    n_correct = 0
    for i, t in enumerate(truth):
        if i >= len(got):
            print(f"row {i+1}: MISSING (expected {t['date']} {t['desc']})")
            continue
        g = got[i]
        ok = (g.date == t["date"] and g.description == t["desc"]
              and (g.debit or "") == (t["debit"] or "")
              and (g.credit or "") == (t["credit"] or "")
              and (g.balance or "") == (t["balance"] or ""))
        if ok:
            n_correct += 1
        else:
            print(f"row {i+1}: got {g.date} {g.description!r} "
                  f"debit={g.debit!r} credit={g.credit!r} balance={g.balance!r}")
            print(f"         want {t['date']} {t['desc']!r} "
                  f"debit={t['debit']!r} credit={t['credit']!r} balance={t['balance']!r}")
    if len(got) > len(truth):
        print(f"{len(got) - len(truth)} extra rows extracted")
    print(f"\nOCR: {n_correct}/{len(truth)} rows fully correct "
          f"({n_correct / len(truth):.0%}), extracted {len(got)} rows")
    return 0 if n_correct == len(truth) else 1


if __name__ == "__main__":
    sys.exit(main())
