# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF_DIR = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf")
doc = fitz.open(PDF_DIR / "KR0082_DB생명보험.pdf")
for p in [26, 28]:
    print(f"--- DB page {p+1} ---")
    print(doc[p].get_text())
doc.close()
