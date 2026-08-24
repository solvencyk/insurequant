# -*- coding: utf-8 -*-
"""Render the already-located TFI pages for AIA(KR0080)/KB(KR0010)/KR0005 so the
item52(지급여력금액, TFI표) row -- printed right above 기본자본(item50) -- can be
read visually. Page numbers reused from fix_20260822_aia_kb_backlog.py's
SOURCE_PAGE dict (already vision-verified for items 47-51) and
fix_20260822_singles_backlog.py's KR0005 note (p41 1-idx)."""
from __future__ import annotations
import sys, os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\2e98dd9e-be51-411e-a455-ce573b8bf95c\scratchpad\item52_vision")
OUT.mkdir(parents=True, exist_ok=True)
sys.stdout = os.fdopen(1, "w", encoding="utf-8", closefd=False)

import fitz  # noqa: E402
fitz.TOOLS.mupdf_display_errors(False)
fitz.TOOLS.mupdf_display_warnings(False)

TARGETS = [
    ("KR0080", "2024.4Q", r"data\disclosure\FY2024_Q4\raw\KR0080_에이아이에이생명보험.pdf", 54, 300),
    ("KR0080", "2025.1Q", r"data\disclosure\FY2025_Q1\raw\KR0080_에이아이에이생명보험.pdf", 17, 300),
    ("KR0080", "2025.2Q", r"data\disclosure\FY2025_Q2\raw\KR0080_에이아이에이생명보험.pdf", 18, 300),
    ("KR0080", "2025.3Q", r"data\disclosure\FY2025_Q3\raw\KR0080_에이아이에이생명보험.pdf", 17, 300),
    ("KR0080", "2025.4Q", r"data\disclosure\FY2025_Q4\raw\KR0080_에이아이에이생명보험.pdf", 59, 300),
    ("KR0080", "2026.1Q", r"data\disclosure\FY2026_Q1\raw\KR0080_에이아이에이생명보험.pdf", 19, 300),
    ("KR0010", "2024.1Q", r"data\disclosure\FY2024_Q1\raw\KR0010_KB손해보험_amended.pdf", 14, 300),
    ("KR0010", "2024.3Q", r"data\disclosure\FY2024_Q3\raw\KR0010_KB손해보험_amended.pdf", 14, 300),
    ("KR0010", "2025.3Q", r"data\disclosure\FY2025_Q3\raw\KR0010_KB손해보험.pdf", 17, 300),
    ("KR0010", "2025.4Q", r"data\disclosure\FY2025_Q4\raw\KR0010_KB손해보험.pdf", 69, 300),
    ("KR0010", "2026.1Q", r"data\disclosure\FY2026_Q1\raw\KR0010_KB손해보험.pdf", 18, 300),
    ("KR0005", "2024.4Q", r"data\disclosure\FY2024_Q4\raw\KR0005_흥국화재.pdf", 40, 280),  # p41(1-idx)
]

for code, q, rel, page0, dpi in TARGETS:
    pdf_path = REPO / rel
    doc = fitz.open(pdf_path)
    pix = doc[page0].get_pixmap(dpi=dpi)
    out_path = OUT / f"{code}_{q}_p{page0}_dpi{dpi}.png"
    pix.save(str(out_path))
    print(f"{code} {q}: saved {out_path} ({pix.width}x{pix.height})")
    doc.close()
