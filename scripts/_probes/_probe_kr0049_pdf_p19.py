# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

doc = fitz.open("data/disclosure/FY2026_Q2/pdf/KR0049_악사손해보험.pdf")
page = doc[18]  # 0-indexed page 19
print(page.get_text())
