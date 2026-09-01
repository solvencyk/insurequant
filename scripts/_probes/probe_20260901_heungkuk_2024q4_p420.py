# -*- coding: utf-8 -*-
"""Second cluster of 지급여력비율/K-ICS hits in Heungkuk 2024.4Q raw PDF (pages
420-424, 437). Dump to see whether this bundle has an abbreviated K-ICS summary
(headline ratio only) vs the full 정기경영공시-style ①②③ transition breakdown."""
import io
import sys

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2024_Q4\raw\KR0071_흥국생명보험.pdf"

doc = fitz.open(PDF)
for pno in (419, 420, 421, 422, 423, 424, 437):
    t = doc[pno - 1].get_text()
    print(f"\n===== p{pno} (chars={len(t)}) =====")
    print(t[:2000])
doc.close()
