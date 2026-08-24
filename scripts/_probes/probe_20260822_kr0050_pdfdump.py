# -*- coding: utf-8 -*-
"""Read-only probe: dump KR0050 2023.1Q amended PDF page-by-page, search individual keywords."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = REPO / "data" / "disclosure" / "FY2023_Q1" / "raw" / "KR0050_하나손해보험_amended.pdf"

doc = fitz.open(PDF)
page_texts = [doc[i].get_text() for i in range(doc.page_count)]
doc.close()

print(f"PDF: {PDF.name}  pages={len(page_texts)}")
print()

KEYWORDS = ["경과조치", "공통적용", "보완자본", "기본자본", "한도", "해약환급금", "지급여력기준금액",
            "지급여력금액", "선택적용"]

print("=== 페이지별 키워드 등장 여부 ===")
for i, t in enumerate(page_texts):
    hits = [kw for kw in KEYWORDS if kw in t]
    print(f"  p{i} (chars={len(t)}): {hits}")

print()
print("=== 페이지별 전체 텍스트 ===")
for i, t in enumerate(page_texts):
    print(f"\n{'='*20} PAGE {i} (0-idx) / {i+1} (1-idx), chars={len(t)} {'='*20}")
    print(t)
