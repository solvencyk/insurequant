# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF_DIR = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf")
for fname, pages in [
    ("KR0070_에이비엘생명보험.pdf", [30, 32]),
    ("KR0082_DB생명보험.pdf", [25, 27]),
]:
    doc = fitz.open(PDF_DIR / fname)
    print(f"===== {fname} =====")
    for p in pages:
        t = doc[p].get_text()
        print(f"--- page {p+1} textlen={len(t)} ---")
        print(t)
    doc.close()
