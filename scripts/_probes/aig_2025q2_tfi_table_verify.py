# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2025_Q2\raw\KR0029_AIG손해보험.pdf"
doc = fitz.open(PDF)
target_page = None
for i, page in enumerate(doc):
    if "기발행" in page.get_text():
        target_page = i
        break
print(f"found on page {target_page+1 if target_page is not None else None}")
if target_page is not None:
    page = doc[target_page]
    print(page.get_text())
    print("--- word coords ---")
    words = page.get_text("words")
    words_sorted = sorted(words, key=lambda w: (round(w[1],1), w[0]))
    for w in words_sorted:
        if 130 <= w[1] <= 420:  # narrow to the TFI table y-range roughly
            print(f"y={w[1]:7.1f} x={w[0]:7.1f}  {w[4]}")
