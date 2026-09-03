# -*- coding: utf-8 -*-
"""3개 의심회사(KR0010/KR0079/KR0087) 240dpi 렌더 저장 — 스캔본 육안 확인용, 일회성."""
from __future__ import annotations

import sys
from pathlib import Path

import fitz  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "raw"
SCRATCH = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\bf3f149f-63da-4c1f-b00e-c41148decd48\scratchpad"
)

CODES = ["KR0010", "KR0079", "KR0087"]
mat = fitz.Matrix(240 / 72, 240 / 72)

all_pdfs = sorted(PDF_DIR.glob("*.pdf"))
for code in CODES:
    matches = [p for p in all_pdfs if p.name.startswith(code + "_")]
    if not matches:
        print(f"{code}: NOT FOUND")
        continue
    path = matches[0]
    doc = fitz.open(str(path))
    pages_to_render = sorted({0, doc.page_count // 2, doc.page_count - 1})
    for pageno in pages_to_render:
        pix = doc[pageno].get_pixmap(matrix=mat)
        out = SCRATCH / f"{code}_p{pageno + 1}.png"
        pix.save(str(out))
        print(f"{code} page {pageno + 1}/{doc.page_count} -> {out} ({pix.width}x{pix.height})")
    doc.close()
