# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz  # PyMuPDF

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2025_Q2\raw\KR0029_AIG손해보험.pdf"
doc = fitz.open(PDF)
print(f"pages: {doc.page_count}")

keywords = ["금리위험액", "주식위험액", "부동산위험액", "외환위험액", "자산집중위험액", "시장위험 관리", "6-4"]
for i, page in enumerate(doc):
    text = page.get_text()
    hits = [kw for kw in keywords if kw in text]
    if hits:
        print(f"--- page {i+1} (0-idx {i}): hits={hits} chars={len(text)} ---")
