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
KEYS = ["사망위험액", "장수위험액", "장해", "해지위험액", "사업비위험액", "대재해위험액",
        "금리위험액", "주식위험액", "부동산위험액", "외환위험액", "자산집중위험액",
        "순자산가치(충격전)", "순자산가치(평균회귀)"]
for i in range(0, 70):
    t = doc[i].get_text()
    hits = [k for k in KEYS if k in t]
    if hits:
        print(i + 1, hits)
