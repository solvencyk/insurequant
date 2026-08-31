# -*- coding: utf-8 -*-
import io
import sys

import fitz
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

cands = list(Path("data/disclosure/FY2024_Q4/raw").glob("KR0079_*.pdf"))
print("candidates:", cands)
PDF = str(cands[0])
doc = fitz.open(PDF)
print("pages:", doc.page_count)
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "사망위험액" in t or "장수위험액" in t or "장해" in t and "질병위험액" in t:
        print(i + 1, repr(t[:200].replace(chr(10), " | ")))
        print("----")
