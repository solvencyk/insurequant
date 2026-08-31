# -*- coding: utf-8 -*-
"""Dump raw text of PDF page 19 (0-idx 18) — the ④ 금리위험 경과조치 table for KR0005 2026.2Q."""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # noqa: E402

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0005_흥국화재.pdf")

doc = fitz.open(PDF)
for idx in (17, 18, 19):
    page = doc[idx]
    print(f"===== PAGE index={idx} (PDF page {idx+1}) =====")
    print(page.get_text())
    print()
