#!/usr/bin/env python3
"""Check native text layer density around the 금리민감도 table in KB손해보험 2026.2Q raw PDF."""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[2]
pdf_path = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf" / "KR0010_KB손해보험.pdf"

doc = fitz.open(pdf_path)
print(f"pages={doc.page_count}")
for i, page in enumerate(doc):
    text = page.get_text()
    if "민감도" in text or "위험 민감도" in text.replace(" ", ""):
        print(f"page {i+1}: text_len={len(text)}  has_민감도=True")
    if "지급여력기준금액" in text and ("195" in text or "187.45" in text or "72,787" in text or "72787" in text):
        print(f"  ^ candidate table page {i+1}")

print()
print("=== text density per page (chars) for pages 1..40 ===")
for i in range(min(40, doc.page_count)):
    t = doc[i].get_text()
    print(f"  p{i+1}: {len(t)} chars")
