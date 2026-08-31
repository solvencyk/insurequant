# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

path = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR1000_코리안리재보험.pdf"
doc = fitz.open(path)
print(f"page_count={doc.page_count}")

keywords = ["금리위험액", "주식위험액", "부동산위험액", "6-4", "시장위험 관리", "순자산가치"]
for i, page in enumerate(doc):
    text = page.get_text()
    hits = [k for k in keywords if k in text]
    if hits:
        print(f"--- page {i+1} (0-idx {i}) hits={hits} chars={len(text)}")
