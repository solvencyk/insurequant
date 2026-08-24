# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

jobs = [
    ("2023.3Q", "FY2023_Q3", [8]),
    ("2023.4Q", "FY2023_Q4", [17, 18]),
    ("2024.1Q", "FY2024_Q1", [8, 9]),
    ("2024.2Q", "FY2024_Q2", [8, 9]),
    ("2024.3Q", "FY2024_Q3", [8, 9]),
]
for label, period, idxs in jobs:
    pdf = ROOT / "data/disclosure" / period / "raw" / "KR1000_코리안리.pdf"
    doc = fitz.open(pdf)
    print(f"\n\n#################### {label} ####################")
    for i in idxs:
        print(f"--- page idx {i} ---")
        print(doc[i].get_text())
    doc.close()
