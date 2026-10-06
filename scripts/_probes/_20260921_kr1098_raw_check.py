# -*- coding: utf-8 -*-
"""Check raw PDF text (fitz, no rendering) for KR1098 2026.2Q rate-sensitivity table
to see the TRUE label characters docling may have garbled in the MD."""
import io, sys, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
pdfs = glob.glob(ROOT + "data/disclosure/FY2026_Q2/*/KR1098_*.pdf")
print("pdfs found:", pdfs)
doc = fitz.open(pdfs[0])
target = None
for i in range(doc.page_count):
    t = doc.load_page(i).get_text()
    if "금리" in t and "민감도" in t and "분석" in t:
        target = i
        print(f"page {i} (0-idx) has 금리민감도분석")
        break
if target is not None:
    page = doc.load_page(target)
    print("---- raw text dump of that page ----")
    print(page.get_text())
doc.close()
