# -*- coding: utf-8 -*-
import io
import sys
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0095_메트라이프생명보험.pdf"
doc = fitz.open(PDF)
print("n_pages:", doc.page_count)

keywords = ["금리위험액 현황", "① 금리위험액", "순자산가치", "충격전", "평균회귀", "금리상승", "금리하락",
            "금리평탄", "금리경사", "주식위험액 현황", "부동산위험액 현황"]

for i in range(doc.page_count):
    page = doc[i]
    text = page.get_text()
    hits = [k for k in keywords if k in text]
    if hits:
        print(f"--- page {i+1} (0-idx {i}) chars={len(text)} hits={hits}")
