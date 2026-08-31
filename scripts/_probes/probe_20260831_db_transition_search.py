# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF_DIR = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf")
doc = fitz.open(PDF_DIR / "KR0082_DB생명보험.pdf")
for i in range(doc.page_count):
    t = doc[i].get_text().replace(" ", "")
    if "주식위험경과조치" in t or "금리위험경과조치" in t:
        print(f"page {i+1}")
        print(doc[i].get_text())
doc.close()
