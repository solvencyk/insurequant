# -*- coding: utf-8 -*-
import io
import sys
from pathlib import Path

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

cands = list(Path("data/disclosure/FY2024_Q4/raw").glob("KR0079_*.pdf"))
PDF = str(cands[0])
doc = fitz.open(PDF)
print("pages:", doc.page_count)
hit_pages = []
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "지급여력" in t:
        hit_pages.append(i + 1)
print("지급여력 hit pages:", hit_pages[:60], "... total", len(hit_pages))
