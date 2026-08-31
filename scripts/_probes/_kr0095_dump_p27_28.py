# -*- coding: utf-8 -*-
import io
import sys
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0095_메트라이프생명보험.pdf"
doc = fitz.open(PDF)
for idx in (25, 26, 27, 28):  # 0-indexed pages 26,27,28,29 (1-indexed) -> print 26-29
    page = doc[idx]
    print(f"===================== PAGE {idx+1} (1-indexed) =====================")
    print(page.get_text())
