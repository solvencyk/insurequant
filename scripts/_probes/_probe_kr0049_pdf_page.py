# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

doc = fitz.open("data/disclosure/FY2026_Q2/pdf/KR0049_악사손해보험.pdf")
print("pages:", doc.page_count)
for i, page in enumerate(doc):
    text = page.get_text()
    if "보완자본 한도" in text and "해약환급금" in text:
        print(f"--- page {i+1} (0-idx {i}) has 보완자본 한도 + 해약환급금 ---")
