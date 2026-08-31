# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

path = r"data/disclosure/FY2026_Q2/pdf/KR0087_동양생명.pdf"
doc = fitz.open(path)
for i, page in enumerate(doc):
    text = page.get_text()
    n = len(text.strip())
    tag = ""
    if "지급여력" in text:
        tag += " [지급여력]"
    if n > 50:
        tag += f" [TEXT n={n}]"
    if tag:
        print(i+1, tag, repr(text[:60]))
