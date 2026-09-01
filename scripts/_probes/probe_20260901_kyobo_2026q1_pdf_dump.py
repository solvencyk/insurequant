# -*- coding: utf-8 -*-
"""Dump raw text of pages 11, 13-16 of the Kyobo 2026.1Q PDF (the transition-detail
pages docling's MD conversion apparently dropped) so we can read the ②/③ tables
directly. Read-only."""
import io
import sys

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q1\raw\KR0073_교보생명보험.pdf"

doc = fitz.open(PDF)
for pno in (11, 12, 13, 14, 15, 16):
    page = doc[pno - 1]
    print(f"\n===== PAGE {pno} =====")
    print(page.get_text())
doc.close()
