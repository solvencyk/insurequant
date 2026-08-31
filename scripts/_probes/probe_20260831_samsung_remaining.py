# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0069_삼성생명.pdf")
doc = fitz.open(PDF)
print(f"total pages: {doc.page_count}")
needles = ["대재해위험액", "부동산위험액현황", "외환위험액현황", "자산집중위험액현황", "전염병위험액"]
for i in range(doc.page_count):
    t = doc[i].get_text().replace(" ", "")
    hits = [n for n in needles if n in t]
    if hits:
        print(f"page {i+1}: {hits}")
doc.close()
