# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

PDF = r"data/disclosure/FY2026_Q2/pdf/KR0074_라이나생명보험.pdf"
doc = fitz.open(PDF)
print(doc[17].get_text())
