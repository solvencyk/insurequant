# -*- coding: utf-8 -*-
"""Dump full text of KR0032 2026.2Q raw PDF pages 31-39 (1-indexed) via fitz."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0032_NH농협손해보험.pdf"

doc = fitz.open(PDF)

START = int(sys.argv[1]) if len(sys.argv) > 1 else 31
END = int(sys.argv[2]) if len(sys.argv) > 2 else 39

for i in range(START - 1, END):
    print(f"\n{'='*20} PAGE {i+1} {'='*20}")
    print(doc[i].get_text())
