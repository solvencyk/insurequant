# -*- coding: utf-8 -*-
"""Heungkuk 2024.4Q: scan_pairs() found no item22/23 row on any page. Dump the
raw text of every page that mentions 경과조치 + 장수위험/주식위험/금리위험, plus
every page mentioning 기타요구자본 anywhere, to see whether the row label or
layout differs from the other quarters (e.g. split across lines) or the section
is genuinely absent this quarter. Read-only."""
import io
import sys

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2024_Q4\raw\KR0071_흥국생명보험.pdf"

doc = fitz.open(PDF)
print(f"pages={doc.page_count}")
for i, page in enumerate(doc):
    text = page.get_text()
    has_gc = "경과조치" in text
    has_any = any(k in text for k in ("장수위험", "주식위험", "금리위험"))
    has_other = "기타요구자본" in text or "기타 요구자본" in text
    if has_gc or has_other:
        print(f"\n--- page {i+1}  경과조치={has_gc} any={has_any} 기타요구자본={has_other} ---")
        if has_gc or has_other:
            print(text)
doc.close()
