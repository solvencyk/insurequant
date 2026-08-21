# -*- coding: utf-8 -*-
"""Render specific pages of KR0071 2024.4Q raw PDF at high DPI for visual reading."""
import sys
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "data" / "disclosure" / "FY2024_Q4" / "raw" / "KR0071_흥국생명보험.pdf"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\c9c7c053-f96a-4878-bcb0-5ff8567de9fd\scratchpad\kr0071_pages")
OUT.mkdir(parents=True, exist_ok=True)

# 1-indexed physical page numbers to render
pages_1idx = [43, 44, 45, 46, 47, 48, 49, 50, 51, 52]
dpi = 260

doc = fitz.open(str(PDF))
print(f"total pages: {doc.page_count}")
mat = fitz.Matrix(dpi / 72, dpi / 72)
for p1 in pages_1idx:
    idx = p1 - 1
    if not (0 <= idx < doc.page_count):
        print(f"page {p1}: OUT OF RANGE")
        continue
    page = doc[idx]
    txt = page.get_text()
    pix = page.get_pixmap(matrix=mat)
    out_path = OUT / f"p{p1:03d}.png"
    pix.save(str(out_path))
    print(f"page {p1}: rendered {pix.width}x{pix.height} -> {out_path}  (native chars={len(txt)})")
doc.close()
