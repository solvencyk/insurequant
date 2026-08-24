# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\c9c7c053-f96a-4878-bcb0-5ff8567de9fd\scratchpad\render")
OUT.mkdir(parents=True, exist_ok=True)

PDF = ROOT / "data/disclosure/FY2024_Q4/raw/KR0071_흥국생명보험.pdf"
pages_1idx = list(range(43, 53))
dpi = 260

doc = fitz.open(str(PDF))
print(f"total pages: {doc.page_count}")
mat = fitz.Matrix(dpi / 72, dpi / 72)
for p1 in pages_1idx:
    idx = p1 - 1
    if not (0 <= idx < doc.page_count):
        continue
    page = doc[idx]
    pix = page.get_pixmap(matrix=mat)
    out_path = OUT / f"kr0071_2024q4_p{p1:03d}.png"
    pix.save(str(out_path))
    print(f"page {p1}: {pix.width}x{pix.height}")
doc.close()
