#!/usr/bin/env python3
"""Locate + dump raw PDF text/words for the 금리 민감도 분석 table, 예별손해보험 2024.4Q."""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[2]
pdf_path = ROOT / "data" / "disclosure" / "FY2024_Q4" / "raw" / "KR0004_예별손해보험.pdf"

doc = fitz.open(pdf_path)
print(f"pages={doc.page_count}")
target_page = None
for i, page in enumerate(doc):
    text = page.get_text()
    if "금리 민감도 분석" in text.replace("\n", "") or ("금리" in text and "민감도" in text and "기준금액" in text):
        print(f"--- page {i+1} candidate ---")
        target_page = i

for i, page in enumerate(doc):
    text = page.get_text()
    if "지급여력기준금액" in text and "9,170" in text:
        print(f"\n===== FULL TEXT page {i+1} (contains 지급여력기준금액 + 9,170) =====")
        print(text)
        print("\n===== WORDS with bbox (sorted by y then x) =====")
        words = page.get_text("words")  # (x0,y0,x1,y1, word, block,line,word_no)
        words_sorted = sorted(words, key=lambda w: (round(w[1], 1), w[0]))
        for w in words_sorted:
            print(f"  y={w[1]:.1f} x={w[0]:.1f}  '{w[4]}'")
