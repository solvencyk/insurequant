#!/usr/bin/env python3
"""Render K-ICS raw PDF pages for direct vision reading (no OCR engine).

2026-09-01 decision (inbox `20260901T0420Z`): for a *specific, small* cohort of
`SCANNED_SECTION` cells, rendering pages with fitz and reading them directly (Claude
vision via the Read tool) beat every EasyOCR path tried -- docling-routed OCR tops out
at 5/9 correct even at its least-bad scale (see `ocr_parse_scanned_disclosure.py`
`_ocr_converter` docstring). This script is the reusable half of that workflow: it only
renders (single pages at a chosen dpi, or a contact-sheet grid of low-res thumbnails for
scanning many pages quickly to *locate* a section before reading it at full res). It does
not call any OCR engine and writes no output back to any master -- read the PNGs it
writes, transcribe by hand, cross-check against K-ICS identities before writing a patch.

usage:
  # single page at 200dpi
  PY scripts/_probes/render_kics_page.py FY2024_Q4 KR0071 --page 44 --dpi 200 --out out.png

  # contact sheet of a page range at low dpi, to locate a section fast
  PY scripts/_probes/render_kics_page.py FY2024_Q4 KR0071 --pages 30 60 --dpi 100 --cols 4 --out sheet.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import fitz  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402


def _open(fyq: str, code: str) -> fitz.Document:
    cands = disclosure_pdfs(fyq, code)
    if not cands:
        raise SystemExit(f"no raw PDF found for {code} {fyq}")
    print(f"using: {cands[0]}")
    return fitz.open(cands[0])


def render_single(doc: fitz.Document, page_1idx: int, dpi: int, out: Path) -> None:
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = doc[page_1idx - 1].get_pixmap(matrix=mat)
    pix.save(out)
    print(f"wrote {out} (page {page_1idx}, {dpi}dpi, {pix.width}x{pix.height})")


def render_contact_sheet(doc: fitz.Document, start: int, end: int, dpi: int, cols: int, out: Path) -> None:
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    thumbs, labels = [], []
    for p in range(start, end + 1):
        if p < 1 or p > doc.page_count:
            continue
        pix = doc[p - 1].get_pixmap(matrix=mat)
        thumbs.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        labels.append(p)
    if not thumbs:
        raise SystemExit("no pages rendered (bad range?)")
    w, h = thumbs[0].size
    rows = (len(thumbs) + cols - 1) // cols
    pad, label_h = 4, 22
    sheet = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + label_h + pad) + pad), "white")
    draw = ImageDraw.Draw(sheet)
    for i, (img, lbl) in enumerate(zip(thumbs, labels)):
        r, c = divmod(i, cols)
        x, y = pad + c * (w + pad), pad + r * (h + label_h + pad)
        draw.rectangle([x, y, x + w, y + label_h - 2], fill=(30, 30, 30))
        draw.text((x + 4, y + 3), f"p{lbl}", fill=(255, 255, 0))
        sheet.paste(img, (x, y + label_h))
    sheet.save(out)
    print(f"wrote {out} pages {start}-{end} ({len(thumbs)} thumbs, {cols} cols, {dpi}dpi)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("period", help="e.g. FY2024_Q4")
    ap.add_argument("company", help="KR#### code")
    ap.add_argument("--page", type=int, help="single page, 1-indexed")
    ap.add_argument("--pages", type=int, nargs=2, metavar=("START", "END"), help="contact-sheet range, 1-indexed inclusive")
    ap.add_argument("--dpi", type=int, default=180)
    ap.add_argument("--cols", type=int, default=4, help="contact-sheet columns")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    doc = _open(args.period, args.company)
    try:
        if args.page:
            render_single(doc, args.page, args.dpi, args.out)
        elif args.pages:
            render_contact_sheet(doc, args.pages[0], args.pages[1], args.dpi, args.cols, args.out)
        else:
            raise SystemExit("pass --page N or --pages START END")
    finally:
        doc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
