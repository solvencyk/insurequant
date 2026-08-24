# -*- coding: utf-8 -*-
"""Dump the headline table (경과조치 적용전 지급여력비율 세부) AND the TFI table for
KR0003 2023.1Q / 2024.4Q / 2025.1Q, side by side. Read-only. 2026-08-22."""
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

jobs = [
    ("2023.1Q", ROOT / "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf"),
    ("2024.4Q", ROOT / "data/disclosure/FY2024_Q4/raw/KR0003_롯데손해보험.pdf"),
    ("2025.1Q", ROOT / "data/disclosure/FY2025_Q1/raw/KR0003_롯데손해보험.pdf"),
]
for label, pdf in jobs:
    doc = fitz.open(pdf)
    print(f"\n\n#################### {label} {pdf.name} pages={doc.page_count} ####################")
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if ("가. 지급여력금액" in t) or ("공통적용" in t and "보완자본" in t and "한도" in t):
            print(f"=== page idx {i} (printed {i+1}) ===")
            print(t)
    doc.close()
