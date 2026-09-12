# -*- coding: utf-8 -*-
"""Render KR0079 2023.4Q raw PDF p36 (1-indexed, the TFI table page per
fix_20260901_kr0079_scanned_section_tier2.py's own docstring) at 190dpi so it
can be read visually -- ticket 2 asks to independently re-verify item54
(기발행 후순위채무) before applying the DATA fix (496.50 -> 3003.59).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import fitz  # noqa: E402

PDF = ROOT / "data/disclosure/FY2023_Q4/raw/KR0079_미래에셋생명_amended.pdf"
OUT = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a58c26ac-9516-4250-9994-281cfa9a1766\scratchpad")
OUT.mkdir(parents=True, exist_ok=True)

doc = fitz.open(PDF)
print(f"page_count={doc.page_count}")
for pno in (34, 35, 36):  # 0-indexed p35/p36/p37 == printed p36 +/- 1, scan a small window
    if pno >= doc.page_count:
        continue
    page = doc[pno]
    text = page.get_text()
    print(f"--- 0-idx page {pno} (printed ~{pno+1}) chars={len(text)} ---")
    if text.strip():
        print(text[:300])
    mat = fitz.Matrix(190 / 72, 190 / 72)
    pix = page.get_pixmap(matrix=mat)
    out_path = OUT / f"kr0079_2023q4_p{pno+1}.png"
    pix.save(str(out_path))
    print(f"saved {out_path}")
doc.close()
