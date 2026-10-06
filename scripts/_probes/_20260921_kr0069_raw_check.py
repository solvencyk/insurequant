# -*- coding: utf-8 -*-
import io, sys, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
pdfs = glob.glob(ROOT + "data/disclosure/FY2026_Q2/*/KR0069_*.pdf")
print("pdfs:", pdfs)
doc = fitz.open(pdfs[0])
target = None
for i in range(doc.page_count):
    t = doc.load_page(i).get_text()
    if "금리" in t and "민감도" in t and "분석" in t and "기준금액" in t:
        target = i
        print(f"page idx {i} candidate")
if target is not None:
    print("---- full text of last matching page ----")
    print(doc.load_page(target).get_text())
doc.close()
