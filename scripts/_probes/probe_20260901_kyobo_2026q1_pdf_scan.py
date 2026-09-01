# -*- coding: utf-8 -*-
"""Probe: does the raw Kyobo 2026.1Q PDF contain the [선택적용 경과조치 관련] ②/③
tables that are missing from the docling MD (md_inbox/FY2026_Q1/KR0073_...md ends at
line 463, right after the [경과조치 적용 전 지급여력비율 세부] table)?

Read-only. Prints per-page text length + keyword hits so we can tell a genuine
docling-conversion gap (source has the section, MD lost it) from a source that
never printed it in the first place.
"""
import io
import sys

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q1\raw\KR0073_교보생명보험.pdf"

doc = fitz.open(PDF)
print(f"pages={doc.page_count}")
for i, page in enumerate(doc):
    text = page.get_text()
    n = len(text)
    hits = []
    for kw in ("경과조치", "선택적용", "장수위험", "기타요구자본", "지급여력비율의 경과조치"):
        if kw in text:
            hits.append(kw)
    if hits or n < 200:
        print(f"p{i+1:>3} chars={n:>5}  hits={hits}")
doc.close()
