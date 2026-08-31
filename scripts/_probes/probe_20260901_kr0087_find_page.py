# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

path = r"data/disclosure/FY2026_Q2/pdf/KR0087_동양생명.pdf"
doc = fitz.open(path)
print("page count:", len(doc))
for i, page in enumerate(doc):
    text = page.get_text()
    if "해약환급금" in text or ("보완자본" in text and "한도" in text):
        print(f"--- page {i+1} (0-idx {i}) --- chars={len(text)}")
