# -*- coding: utf-8 -*-
import io
import sys

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

doc = fitz.open(r"data/disclosure/FY2026_Q1/raw/KR0087_동양생명.pdf")
for i in range(doc.page_count):
    t = doc[i].get_text()
    print(f"page {i}: {len(t)} chars")
