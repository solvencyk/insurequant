# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pdf = ROOT / "data/disclosure/FY2023_Q2/raw/KR0080_에이아이에이생명보험.pdf"
doc = fitz.open(pdf)
print("pages", doc.page_count)
for i in range(doc.page_count):
    t = doc[i].get_text()
    hit = []
    for kw in ["29,645", "4,147", "가. 지급여력금액", "지급여력금액"]:
        if kw in t:
            hit.append(kw)
    if hit:
        print(f"page idx {i}: {hit}")
doc.close()
