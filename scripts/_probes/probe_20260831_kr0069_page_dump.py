# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0069_삼성생명.pdf")
doc = fitz.open(PDF)
for pno in [15,16,17,18,19,20,21]:  # 0-idx, i.e. pages 16-22 (1-idx)
    text = doc[pno].get_text()
    print(f"===== page {pno+1} (1-idx) textlen={len(text)} =====")
    print(text)
    print()
doc.close()
