# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF_DIR = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf")

for fname, pages in [
    ("KR1011_IBK연금보험.pdf", [19, 20, 24, 25]),
    ("KR0001_메리츠화재해상보험.pdf", [21, 22]),
]:
    doc = fitz.open(PDF_DIR / fname)
    print(f"===== {fname} =====")
    for p in pages:
        t = doc[p].get_text()
        print(f"--- page {p+1} textlen={len(t)} ---")
        print(t)
    doc.close()
