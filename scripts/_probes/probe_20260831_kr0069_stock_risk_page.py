# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0069_삼성생명.pdf")
doc = fitz.open(PDF)
for pno in range(doc.page_count):
    t = doc[pno].get_text()
    if "주식위험액" in t.replace(" ", ""):
        print(f"===== page {pno+1} textlen={len(t)} =====")
        print(t)
        print()
doc.close()
