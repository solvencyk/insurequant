# -*- coding: utf-8 -*-
import sys, io
from pathlib import Path
import fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
pdf_path = list((ROOT/"data"/"disclosure"/"FY2024_Q4"/"raw").glob("KR1098_*.pdf"))[0]
print(f"file: {pdf_path}")
doc = fitz.open(str(pdf_path))
print(f"pages: {len(doc)}")
for pno in range(len(doc)):
    text = doc[pno].get_text()
    print(f"  page {pno+1}: chars={len(text)}")
doc.close()
