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
for i in range(0, 70):
    t = doc[i].get_text()
    n = t.count("위험액")
    if n >= 3:
        print(i + 1, "count=", n, repr(t[:150].replace("\n", " | ")))
