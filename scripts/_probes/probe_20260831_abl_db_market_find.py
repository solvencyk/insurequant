# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF_DIR = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf")
for fname in ["KR0070_에이비엘생명보험.pdf", "KR0082_DB생명보험.pdf"]:
    doc = fitz.open(PDF_DIR / fname)
    print(f"===== {fname} ({doc.page_count}p) =====")
    for i in range(doc.page_count):
        t = doc[i].get_text().replace(" ", "")
        if "금리위험액현황" in t or "주식위험액현황" in t:
            print(f"  page {i+1}: 금리={'금리위험액현황' in t} 주식={'주식위험액현황' in t}")
    doc.close()
