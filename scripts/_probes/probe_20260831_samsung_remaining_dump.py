# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0069_삼성생명.pdf")
doc = fitz.open(PDF)
for p in [26, 28, 29, 31, 32, 33]:
    print(f"--- page {p+1} ---")
    print(doc[p].get_text())
doc.close()
