# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pdf = ROOT / "data/disclosure/FY2024_Q4/raw/KR1000_코리안리.pdf"
doc = fitz.open(pdf)
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "공통적용" in t and "보완자본" in t and "한도" in t:
        print(f"=== page idx {i} MATCHED ===")
print("--- full text page 23 ---")
print(doc[23].get_text())
doc.close()
