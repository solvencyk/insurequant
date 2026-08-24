# -*- coding: utf-8 -*-
"""Render specific pages of the backlog PDFs at high DPI for visual reading."""
import sys
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\c9c7c053-f96a-4878-bcb0-5ff8567de9fd\scratchpad\render")
OUT.mkdir(parents=True, exist_ok=True)

JOBS = [
    ("kr0097_2024q2", ROOT / "data/disclosure/FY2024_Q2/raw/KR0097_하나생명보험_amended.pdf", list(range(13, 20)), 220),
]

for tag, pdf, pages_1idx, dpi in JOBS:
    doc = fitz.open(str(pdf))
    print(f"{tag}: total pages={doc.page_count}")
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    for p1 in pages_1idx:
        idx = p1 - 1
        if not (0 <= idx < doc.page_count):
            print(f"  page {p1}: OUT OF RANGE")
            continue
        page = doc[idx]
        pix = page.get_pixmap(matrix=mat)
        out_path = OUT / f"{tag}_p{p1:03d}.png"
        pix.save(str(out_path))
        print(f"  page {p1}: {pix.width}x{pix.height} -> {out_path}")
    doc.close()
