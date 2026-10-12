# -*- coding: utf-8 -*-
"""Read-only: per-page text density + first lines of the KR1102 FY2026_Q1 PDF, to make sure a keyword absence is not a scanned-page artefact."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import fitz
PDF = "C:/Users/sangwook.cho/Desktop/insurequant/data/disclosure/FY2026_Q1/raw/KR1102_스위스리아시아.pdf"
doc = fitz.open(PDF)
for i, pg in enumerate(doc, start=1):
    t = pg.get_text("text", sort=True)
    lines = [l.strip() for l in t.splitlines() if l.strip()]
    imgs = len(pg.get_images(full=True))
    print(f"p{i:02d} chars={len(t):5d} images={imgs} | " + " / ".join(lines[:2])[:110])
