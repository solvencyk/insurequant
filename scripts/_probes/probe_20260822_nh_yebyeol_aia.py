# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

jobs = [
    ("NH농협손해 2024.3Q", ROOT / "data/disclosure/FY2024_Q3/raw/KR0032_NH농협손해보험_amended.pdf"),
    ("예별손해 2025.1Q", ROOT / "data/disclosure/FY2025_Q1/raw/KR0004_예별손해보험.pdf"),
    ("AIA 2023.2Q", ROOT / "data/disclosure/FY2023_Q2/raw/KR0080_에이아이에이생명보험.pdf"),
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
