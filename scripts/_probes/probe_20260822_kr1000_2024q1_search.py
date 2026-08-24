# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pdf = ROOT / "data/disclosure/FY2024_Q1/raw/KR1000_코리안리.pdf"
doc = fitz.open(pdf)
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "공통적용" in t and "보완자본" in t and "한도" in t:
        print("matched", i)
    if "보완자본 한도 적용 전" in t:
        print("  has item47 literal label:", i)
print("--- page idx 10 full ---")
print(doc[10].get_text())
doc.close()
