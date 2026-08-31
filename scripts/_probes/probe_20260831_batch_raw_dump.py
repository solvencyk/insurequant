# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF_DIR = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf")

jobs = [
    ("KR1011_IBK연금보험.pdf", ["사망위험", "장수위험", "생명", "장기손해보험위험액"]),
    ("KR0001_메리츠화재해상보험.pdf", ["사망위험", "장수위험", "생명·장기손해보험위험액"]),
]
for fname, needles in jobs:
    doc = fitz.open(PDF_DIR / fname)
    print(f"===== {fname} ({doc.page_count}p) =====")
    for i in range(doc.page_count):
        t = doc[i].get_text().replace(" ", "")
        hits = [n for n in needles if n.replace(" ", "") in t]
        if hits:
            print(f"  page {i+1}: {hits}")
    doc.close()
