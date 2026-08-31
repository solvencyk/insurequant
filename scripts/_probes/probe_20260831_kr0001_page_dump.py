# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0001_메리츠화재해상보험.pdf")
doc = fitz.open(PDF)
for pno in [13, 14, 15, 16, 17]:
    t = doc[pno].get_text()
    print(f"===== page {pno+1} textlen={len(t)} =====")
    print(t)
    print()
doc.close()
