# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0001_메리츠화재해상보험.pdf")
doc = fitz.open(PDF)
print(f"total pages: {doc.page_count}")
needles = ["지급여력금액으로불인정", "생명장기손해보험위험액", "기본요구자본", "지급여력비율"]
for pno in range(doc.page_count):
    t = doc[pno].get_text().replace(" ", "")
    hits = [k for k in needles if k in t]
    if hits:
        print(f"page {pno+1}: textlen={len(t)}  hits={hits}")
doc.close()
