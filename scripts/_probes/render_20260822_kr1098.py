# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\c9c7c053-f96a-4878-bcb0-5ff8567de9fd\scratchpad\render")
OUT.mkdir(parents=True, exist_ok=True)

JOBS = [
    ("kr1098_q3", ROOT / "data/disclosure/FY2024_Q3/raw/KR1098_카카오페이손해보험.pdf", [10, 11, 12, 13, 14], 220),
    ("kr1098_q2", ROOT / "data/disclosure/FY2024_Q2/raw/KR1098_카카오페이손해보험_amended2.pdf", list(range(1, 46)), 150),
    ("kr1098_q4", ROOT / "data/disclosure/FY2024_Q4/raw/KR1098_카카오페이손해보험.pdf", list(range(1, 62)), 150),
]

for tag, pdf, pages_1idx, dpi in JOBS:
    doc = fitz.open(str(pdf))
    print(f"{tag}: total pages={doc.page_count}")
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    for p1 in pages_1idx:
        idx = p1 - 1
        if not (0 <= idx < doc.page_count):
            continue
        page = doc[idx]
        pix = page.get_pixmap(matrix=mat)
        out_path = OUT / f"{tag}_p{p1:03d}.png"
        pix.save(str(out_path))
    doc.close()
    print(f"  rendered {len(pages_1idx)} pages")
