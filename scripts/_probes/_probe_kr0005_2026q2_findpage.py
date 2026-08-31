# -*- coding: utf-8 -*-
"""Probe: locate the page(s) containing the (2) 선택적용 경과조치 tables (①②③④) in the
KR0005 2026.2Q raw PDF, and dump raw text per page to check whether docling dropped a
numeric cell (e.g. 금리위험 row in table④) that fitz can still see."""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # noqa: E402

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0005_흥국화재.pdf")

doc = fitz.open(PDF)
print(f"n_pages={doc.page_count}")

targets = ["금리위험 경과조치", "주식위험 경과조치", "장수위험", "선택적용 경과조치 관련", "④"]
for i in range(doc.page_count):
    page = doc[i]
    text = page.get_text()
    for t in targets:
        if t in text:
            print(f"page_index={i} (PDF page {i+1}) contains {t!r}")
            break
