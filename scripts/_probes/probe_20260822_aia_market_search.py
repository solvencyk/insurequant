# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pdf = ROOT / "data/disclosure/FY2023_Q2/raw/KR0080_에이아이에이생명보험.pdf"
doc = fitz.open(pdf)
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "시장위험" in t and ("금리위험" in t or "주식위험" in t):
        print(f"=== page idx {i} (printed {i+1}) has 시장위험+금리/주식위험 ===")
doc.close()
