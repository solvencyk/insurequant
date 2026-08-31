#!/usr/bin/env python3
"""Locate + dump raw PDF text for the 금리 민감도 분석 table, 신한이지손해보험 2024.4Q."""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[2]
pdf_path = ROOT / "data" / "disclosure" / "FY2024_Q4" / "raw" / "KR0051_신한이지손해보험.pdf"

doc = fitz.open(pdf_path)
print(f"pages={doc.page_count}")
for i, page in enumerate(doc):
    text = page.get_text()
    if "민감도" in text or "위험민감도" in text:
        print(f"--- page {i+1} (0-idx {i}) contains 민감도 ---")
for i, page in enumerate(doc):
    text = page.get_text()
    if "금리 민감도" in text or "지급여력비율금리" in text.replace(" ", ""):
        print(f"\n===== FULL TEXT page {i+1} =====")
        print(text)
