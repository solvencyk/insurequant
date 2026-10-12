# -*- coding: utf-8 -*-
import re, sys
sys.stdout.reconfigure(encoding="utf-8")
import fitz
doc = fitz.open("C:/Users/sangwook.cho/Desktop/insurequant/data/disclosure/FY2023_Q2/raw/KR0100_처브라이프생명보험.pdf")
NUM = re.compile(r"\d{1,3}(?:,\d{3}){2,}")
for p in (43, 44, 45):
    tx = doc[p - 1].get_text("text")
    toks = [m.group(0) for m in NUM.finditer(tx)]
    print("PAGE", p, "n", len(toks))
    for t in toks:
        v = int(t.replace(",", ""))
        if 1.9e10 <= v <= 2.3e10 or 7.9e11 <= v <= 8.4e11:
            print("   ", t)
