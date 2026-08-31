# -*- coding: utf-8 -*-
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0075_비엔피파리바카디프생명보험.pdf")

doc = fitz.open(PDF)
print("page_count:", doc.page_count)

# find the page(s) with "공통적용" + "보완자본" + "한도"
matched = []
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "공통적용" in t and "보완자본" in t and "한도" in t:
        matched.append(i)
print("matched pages (0-idx):", matched)

for pno in matched:
    page = doc[pno]
    print(f"\n===== PAGE {pno} (1-idx {pno+1}) full text =====")
    print(page.get_text())
doc.close()
