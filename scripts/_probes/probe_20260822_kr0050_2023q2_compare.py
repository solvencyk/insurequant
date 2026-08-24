# -*- coding: utf-8 -*-
"""Read-only probe: KR0050 2023.2Q PDF -- find the '[지급여력비율의 경과조치 적용에 관한 사항]'
   section text, as a contrast case against 2023.1Q (which has no table, prose-only N/A)."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = REPO / "data" / "disclosure" / "FY2023_Q2" / "raw" / "KR0050_하나손해보험_amended.pdf"

doc = fitz.open(PDF)
page_texts = [doc[i].get_text() for i in range(doc.page_count)]
doc.close()

print(f"PDF: {PDF.name}  pages={len(page_texts)}")
for i, t in enumerate(page_texts):
    if "공통적용" in t and "보완자본" in t and "한도" in t:
        print(f"\n----- p{i} (0-idx) -----")
        print(t)
    elif "지급여력비율의 경과조치" in t:
        print(f"\n----- p{i} (0-idx) [섹션헤더만] -----")
        print(t)
