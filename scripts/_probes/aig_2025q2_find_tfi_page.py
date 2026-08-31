# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2025_Q2\raw\KR0029_AIG손해보험.pdf"
doc = fitz.open(PDF)
for i, page in enumerate(doc):
    t = page.get_text()
    if "보완자본 한도" in t:
        print(f"=== page {i+1} ===")
        print(t)
