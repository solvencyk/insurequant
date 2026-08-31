# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
pdf = fitz.open(ROOT / "data/disclosure/FY2025_Q2/raw/KR0029_AIG손해보험.pdf")
print(f"total pages: {pdf.page_count}")
for i in range(pdf.page_count):
    text = pdf[i].get_text()
    if "사망위험" in text or "주식위험액 현황" in text:
        print(f"--- page {i+1} has target keyword ---")
