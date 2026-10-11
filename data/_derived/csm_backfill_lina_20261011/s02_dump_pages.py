# -*- coding: utf-8 -*-
"""Step 2: dump raw text (fitz, reading-order text and word-level lines) of given pages of a KR0074 PDF.
usage: s02_dump_pages.py FY2026_Q2 91 93 96   -> data/_derived/csm_backfill_lina_20261011/pages/<FY>_p<N>.txt (+ prints)
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "pages"
sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)

fy = sys.argv[1]
pages = [int(x) for x in sys.argv[2:]]
OUT.mkdir(exist_ok=True)
pdf = sorted((ROOT / "data" / "disclosure" / fy / "raw").glob("KR0074_*.pdf"))[0]
doc = fitz.open(pdf)
print("PDF", pdf.name, "pages", doc.page_count)
for p in pages:
    page = doc[p - 1]
    txt = page.get_text("text")
    (OUT / f"{fy}_p{p}.txt").write_text(txt, encoding="utf-8", newline="\n")
    print(f"===== {fy} page {p} (rect {page.rect}) =====")
    print(txt)
