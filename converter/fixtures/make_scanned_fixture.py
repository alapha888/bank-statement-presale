"""Build a scanned-style (image-only) fixture from fixture D.

Renders the text-layer fixture-d-text-lines.pdf page to a 300-dpi image
and embeds only the image in a new PDF, so the result has no text layer
-- the same shape as a real scanned statement.

Run:  .venv/bin/python fixtures/make_scanned_fixture.py
Output: fixtures/fixture-s1-scanned.png (rendered page, for OCR)
        fixtures/fixture-s1-scanned.pdf (image-only PDF)
Ground truth: same 6 rows as fixture D (see ground_truth.json).
"""

from __future__ import annotations

from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent


def main() -> None:
    src = pymupdf.open(HERE / "fixture-d-text-lines.pdf")
    page = src[0]
    pix = page.get_pixmap(dpi=300)
    pix.save(HERE / "fixture-s1-scanned.png")
    out = pymupdf.open()
    new_page = out.new_page(width=page.rect.width, height=page.rect.height)
    new_page.insert_image(page.rect, filename=str(HERE / "fixture-s1-scanned.png"))
    out.save(HERE / "fixture-s1-scanned.pdf")
    print(f"rendered {pix.width}x{pix.height} @300dpi -> fixture-s1-scanned.pdf "
          f"(image-only, {len(out)} page)")


if __name__ == "__main__":
    main()
