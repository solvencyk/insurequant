# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2025_Q3\raw\KR0029_AIG손해보험.pdf"
doc = fitz.open(PDF)
page = doc[14]  # page 15, 0-idx 14
print("===== page 15 raw text =====")
print(page.get_text())
print()
print("===== page 15 word-level (x0,y0,text) sorted by y then x =====")
words = page.get_text("words")  # list of (x0,y0,x1,y1,"word",block,line,word_no)
words_sorted = sorted(words, key=lambda w: (round(w[1],1), w[0]))
for w in words_sorted:
    print(f"y={w[1]:7.1f} x={w[0]:7.1f}  {w[4]}")
