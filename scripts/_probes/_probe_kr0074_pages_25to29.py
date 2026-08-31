# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

PDF = r"data/disclosure/FY2026_Q2/pdf/KR0074_라이나생명보험.pdf"
doc = fitz.open(PDF)

for pg in [25, 26, 27, 28, 29]:
    print(f"\n{'='*20} PAGE {pg} {'='*20}")
    text = doc[pg - 1].get_text()
    print(text)
