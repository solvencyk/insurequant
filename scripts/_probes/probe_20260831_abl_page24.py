# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF_DIR = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf")
doc = fitz.open(PDF_DIR / "KR0070_에이비엘생명보험.pdf")
for p in [22, 23, 24]:
    print(f"--- ABL page {p+1} ---")
    print(doc[p].get_text())
doc.close()
