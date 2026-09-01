# -*- coding: utf-8 -*-
"""Dump Heungkuk 2024.4Q raw PDF pages 248-260 and 419-438 (where 지급여력비율/K-ICS/
장수위험 hit but 경과조치/기타요구자본 did not) to see what document this actually is
and whether the transition detail tables are present under a different label."""
import io
import sys

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2024_Q4\raw\KR0071_흥국생명보험.pdf"

doc = fitz.open(PDF)
print(f"pages={doc.page_count}  metadata={doc.metadata}")
for pno in list(range(248, 261)):
    t = doc[pno - 1].get_text()
    print(f"\n===== p{pno} (chars={len(t)}) =====")
    print(t[:1500])
doc.close()
