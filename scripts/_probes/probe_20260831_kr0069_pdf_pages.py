# -*- coding: utf-8 -*-
"""Find which PDF page holds the [경과조치 적용 전 지급여력비율 세부] detail table for KR0069 2026.2Q,
and check it against the docling MD's source_page_ranges."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0069_삼성생명.pdf")
doc = fitz.open(PDF)
print(f"total pages: {doc.page_count}")

needles = ["지급여력비율 세부", "지급여력금액(기본자본", "보통주이외의자본증권", "지급여력기준금액(", "생명장기손해보험위험액"]
for pno in range(doc.page_count):
    text = doc[pno].get_text()
    hits = [n for n in needles if n.replace(" ", "") in text.replace(" ", "")]
    if hits:
        print(f"page {pno+1} (0-idx {pno}): {hits} | textlen={len(text)}")
doc.close()
