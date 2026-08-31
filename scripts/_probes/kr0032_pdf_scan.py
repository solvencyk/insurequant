# -*- coding: utf-8 -*-
"""Scan KR0032 2026.2Q raw PDF for section headers / keyword pages via fitz."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0032_NH농협손해보험.pdf"

doc = fitz.open(PDF)
print(f"total pages: {doc.page_count}")

keywords = [
    "시장위험", "6-4", "6-3", "6-5", "6-6", "6-7",
    "금리위험", "주식위험", "부동산위험", "외환위험", "자산집중위험",
    "위험액 현황", "순자산가치", "충격시나리오", "IRR",
    "지급여력비율의 경과조치", "보완자본 한도", "자본증권",
]

for i in range(doc.page_count):
    text = doc[i].get_text()
    hits = [kw for kw in keywords if kw in text]
    if hits:
        print(f"p{i+1}: {hits}  (chars={len(text)})")
