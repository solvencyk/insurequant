# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1])

jobs = [
    (ROOT / "data/disclosure/FY2024_Q3/raw/KR0075_비엔피파리바카디프생명보험_amended.pdf", 15, "bnp_2024q3.png"),
    (ROOT / "data/disclosure/FY2024_Q4/raw/KR0075_비엔피파리바카디프생명보험.pdf", 49, "bnp_2024q4.png"),
    (ROOT / "data/disclosure/FY2025_Q1/raw/KR0075_비엔피파리바카디프생명보험.pdf", 19, "bnp_2025q1.png"),
]
for pdf, idx, name in jobs:
    doc = fitz.open(pdf)
    pix = doc[idx].get_pixmap(dpi=240)
    outpath = OUT / name
    pix.save(str(outpath))
    print("saved", outpath)
    doc.close()
