# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

path = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR1000_코리안리재보험.pdf"
doc = fitz.open(path)
for pno in [19, 20]:  # 0-indexed -> pages 20, 21
    page = doc[pno]
    print(f"===== PAGE {pno+1} (1-indexed) =====")
    print(page.get_text())
    print()
