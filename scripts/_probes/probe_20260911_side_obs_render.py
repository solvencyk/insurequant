# -*- coding: utf-8 -*-
"""Render candidate pages for the ticket-2 side observations:
  - KR0071 2024.4Q item53/54 (TFI memo rows) -- expect near printed p49
  - KR0010 2025.4Q item8 (자본조정, 세부표) -- expect near printed p67
  - KR0010 2025.4Q item53/54 (TFI memo rows) -- expect near printed p69
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import fitz  # noqa: E402

OUT = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a58c26ac-9516-4250-9994-281cfa9a1766\scratchpad")
OUT.mkdir(parents=True, exist_ok=True)

JOBS = [
    ("kr0071_2024q4", ROOT / "data/disclosure/FY2024_Q4/raw/KR0071_흥국생명보험.pdf", [48, 49, 50]),  # 0-idx
    ("kr0010_2025q4", ROOT / "data/disclosure/FY2025_Q4/raw/KR0010_KB손해보험.pdf", [65, 66, 67, 68, 69, 70]),
]

for tag, pdf, pages in JOBS:
    doc = fitz.open(pdf)
    print(f"{tag}: page_count={doc.page_count}")
    for pno in pages:
        if pno >= doc.page_count:
            continue
        page = doc[pno]
        text = page.get_text()
        mat = fitz.Matrix(190 / 72, 190 / 72)
        pix = page.get_pixmap(matrix=mat)
        out_path = OUT / f"{tag}_p{pno}.png"
        pix.save(str(out_path))
        print(f"  0-idx {pno} (printed ~{pno+1}) chars={len(text)} -> {out_path.name}")
    doc.close()
