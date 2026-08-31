# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import fitz
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
pdf = ROOT / "data/disclosure/FY2024_Q3/raw/KR0080_에이아이에이생명보험.pdf"
doc = fitz.open(pdf)
for pno in (12, 13):
    page = doc[pno]
    words = page.get_text("words")
    rows = {}
    for w in words:
        y = round(w[1] / 4.0) * 4.0
        rows.setdefault(y, []).append((w[0], w[4]))
    print(f"\n########## page {pno+1} ##########")
    for y in sorted(rows):
        cells = sorted(rows[y])
        line = "  |  ".join(f"{x:6.0f}:{t}" for x, t in cells)
        print(f"y={y:7.1f}  {line[:230]}")
