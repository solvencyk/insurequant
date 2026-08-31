# -*- coding: utf-8 -*-
"""KR0080 FY2024_Q3 raw PDF — 다리(bridge) 표 행 좌표 판독."""
import sys, re
from pathlib import Path
import fitz
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
pdf = ROOT / "data/disclosure/FY2024_Q3/raw/KR0080_에이아이에이생명보험.pdf"
doc = fitz.open(pdf)
print("pages =", doc.page_count)
hits = []
for pno in range(doc.page_count):
    t = doc[pno].get_text()
    if "재분류" in t and "불인정" in t:
        hits.append(pno)
print("pages with 재분류+불인정:", hits)
for pno in hits[:3]:
    page = doc[pno]
    words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
    rows = {}
    for w in words:
        y = round(w[1] / 3.0) * 3.0
        rows.setdefault(y, []).append((w[0], w[4]))
    print(f"\n===== page {pno+1} (1-based) =====")
    for y in sorted(rows):
        line = " ".join(t for _, t in sorted(rows[y]))
        if any(k in line for k in ("불인정","재분류","순자산","기본자본","보완자본","지급여력금액")):
            print(f"  y={y:7.1f}  {line[:170]}")
