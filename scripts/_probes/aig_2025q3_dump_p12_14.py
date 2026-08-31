# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2025_Q3\raw\KR0029_AIG손해보험.pdf"
doc = fitz.open(PDF)
for pno in (10, 11, 12, 13):  # pages 11,12,13,14 (0-idx)
    page = doc[pno]
    txt = page.get_text()
    if "건전성감독기준" in txt or "기본자본" in txt or "불인정" in txt:
        print(f"===== page {pno+1} =====")
        print(txt)
        print()
