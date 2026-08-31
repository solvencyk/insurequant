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
for i in range(233, 262):
    t = doc[i].get_text()
    print(f"=== page {i+1} ({len(t)} chars) ===")
    print(t[:400].replace("\n", " | "))
