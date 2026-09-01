# -*- coding: utf-8 -*-
import sys, io
from pathlib import Path
import fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

TARGETS = [
    ("KR0049", "FY2024_Q4"),
    ("KR0049", "FY2025_Q1"),
]
for code, period in TARGETS:
    pdf_path = list((ROOT/"data"/"disclosure"/period/"raw").glob(f"{code}_*.pdf"))[0]
    print(f"\n=== {code} {period}: {pdf_path.name} ===")
    doc = fitz.open(str(pdf_path))
    for pno in range(len(doc)):
        text = doc[pno].get_text()
        if "지급여력기준금액" in text or "기타요구자본" in text or "생명" in text and "장기손해보험위험액" in text:
            print(f"\n--- page {pno+1} ---")
            print(text)
    doc.close()
