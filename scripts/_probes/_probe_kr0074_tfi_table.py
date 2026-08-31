# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

PDF = r"data/disclosure/FY2026_Q2/pdf/KR0074_라이나생명보험.pdf"
doc = fitz.open(PDF)

for i in range(doc.page_count):
    text = doc[i].get_text()
    if "보완자본 한도" in text or "해약환급금 부족분" in text:
        print(f"PAGE {i+1} contains TFI table markers")

kw_pages = []
for i in range(doc.page_count):
    text = doc[i].get_text()
    if "공통적용 경과조치" in text or "선택적용 경과조치" in text:
        kw_pages.append(i+1)
print("경과조치 관련 pages:", kw_pages)
