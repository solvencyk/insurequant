# -*- coding: utf-8 -*-
"""Dump text of KR0097 2024.4Q raw pages 275-330 (1-idx) to find the TFI 공통적용 table."""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "data/disclosure/FY2024_Q4/raw/KR0097_하나생명보험.pdf"
doc = fitz.open(str(PDF))
for p1 in range(275, 331):
    idx = p1 - 1
    if not (0 <= idx < doc.page_count):
        continue
    txt = doc[idx].get_text()
    if len(txt.strip()) < 5:
        continue
    print(f"\n{'='*20} PAGE {p1} (chars={len(txt)}) {'='*20}")
    print(txt)
doc.close()
