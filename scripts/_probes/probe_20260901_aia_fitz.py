# -*- coding: utf-8 -*-
import sys, io
from pathlib import Path
import fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
pdf_path = list((ROOT/"data"/"disclosure"/"FY2024_Q1"/"raw").glob("KR0080_*.pdf"))[0]
print(f"file: {pdf_path}")
doc = fitz.open(str(pdf_path))
print(f"pages: {len(doc)}")
for pno in range(len(doc)):
    text = doc[pno].get_text()
    if "비례성원칙" in text or "관계회사" in text or "종속회사" in text or "기타요구자본" in text:
        print(f"\n--- page {pno+1} ---")
        print(text)
doc.close()
