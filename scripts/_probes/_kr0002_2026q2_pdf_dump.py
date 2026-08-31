# -*- coding: utf-8 -*-
"""Dump full text of specific pages of KR0002 2026.2Q raw PDF."""
import io
import sys
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF_PATH = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0002_한화손해보험.pdf"

pages = [32, 33, 34, 35, 36, 37]

doc = fitz.open(PDF_PATH)
for pno in pages:
    print(f"\n{'='*20} PAGE {pno+1} (0-idx {pno}) {'='*20}")
    print(doc[pno].get_text())
doc.close()
