# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

targets = [
    ("FY2024_Q3", "data/disclosure/FY2024_Q3/raw/KR0075_비엔피파리바카디프생명보험_amended.pdf"),
    ("FY2024_Q4", "data/disclosure/FY2024_Q4/raw/KR0075_비엔피파리바카디프생명보험.pdf"),
    ("FY2025_Q1", "data/disclosure/FY2025_Q1/raw/KR0075_비엔피파리바카디프생명보험.pdf"),
]
for label, relpath in targets:
    pdf = ROOT / relpath
    doc = fitz.open(pdf)
    print(f"\n\n############ {label}  {pdf.name}  pages={doc.page_count} ############")
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if "공통적용" in t and "보완자본" in t and "한도" in t:
            print(f"=== page idx {i} (printed {i+1}) ===")
            print(t)
    doc.close()
