# -*- coding: utf-8 -*-
"""Scan KR0002 2026.2Q raw PDF for 6-4/6-5/6-6 (시장위험/금리위험/신용위험 관리) section pages."""
import io
import sys
import fitz  # PyMuPDF

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF_PATH = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0002_한화손해보험.pdf"

KEYWORDS = [
    "6-4", "6-5", "6-6",
    "시장위험 관리", "금리위험 관리", "신용위험 관리",
    "3-1. 금리위험액", "3-2. 주식위험액", "3-3. 부동산위험액", "3-4. 외환위험액", "3-5. 자산집중위험액",
    "순자산가치", "충격전", "평균회귀", "금리상승", "금리하락", "금리평탄", "금리경사",
]

doc = fitz.open(PDF_PATH)
print(f"total pages: {doc.page_count}")

hits = {}
for pno in range(doc.page_count):
    text = doc[pno].get_text()
    for kw in KEYWORDS:
        if kw in text:
            hits.setdefault(kw, []).append(pno + 1)  # 1-indexed for human reading

print("\n=== keyword -> pages ===")
for kw in KEYWORDS:
    print(f"  {kw!r}: {hits.get(kw, [])}")

doc.close()
