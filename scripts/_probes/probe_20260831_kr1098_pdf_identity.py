# -*- coding: utf-8 -*-
"""Probe: verify actual period content of KR1098 FY2026_Q2 pdf via direct fitz extraction (bypass docling)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

path = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR1098_카카오페이손해보험.pdf"
doc = fitz.open(path)
print(f"pages={doc.page_count}")
for i in range(min(3, doc.page_count)):
    t = doc[i].get_text()
    print(f"--- page {i+1} (len={len(t)}) ---")
    print(t[:800])
print("=== keyword scan (지급여력) per page ===")
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "지급여력" in t or "시장위험" in t or "위험액" in t:
        print(f"p{i+1}: len={len(t)} 지급여력={t.count('지급여력')} 시장위험={t.count('시장위험')} 위험액={t.count('위험액')}")
