# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2025_Q3\raw\KR0029_AIG손해보험.pdf"
doc = fitz.open(PDF)
print(f"pages: {doc.page_count}")
keywords = ["보완자본 한도", "공통적용 경과조치", "지급여력기준금액", "해약환급금"]
for i, page in enumerate(doc):
    text = page.get_text()
    hits = [kw for kw in keywords if kw in text]
    if hits:
        print(f"--- page {i+1} hits={hits} chars={len(text)} ---")
