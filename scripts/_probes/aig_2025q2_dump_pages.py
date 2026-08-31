# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2025_Q2\raw\KR0029_AIG손해보험.pdf"
doc = fitz.open(PDF)
for pno in (27, 28, 29, 30):  # 0-idx for pages 28,29,30,31
    page = doc[pno]
    print(f"===== page {pno+1} =====")
    print(page.get_text())
    print()
