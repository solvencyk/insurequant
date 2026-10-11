# -*- coding: utf-8 -*-
"""Step 90 (read-only): print every row (label | numeric tokens) of given pages of a Lina PDF, plus the first non-numeric lines.
usage: s90_show_rows.py FY2023_Q1 57 58 59"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lina_tbl as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from _disclosure_pdf_paths import latest_disclosure_pdfs  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)

fy = sys.argv[1]
pdf = latest_disclosure_pdfs(fy, "KR0074")[0]
doc = fitz.open(pdf)
print("PDF", pdf.name, "pages", doc.page_count)
for p in [int(x) for x in sys.argv[2:]]:
    pg = doc[p - 1]
    print(f"\n=== {fy} p{p}")
    for r in T.page_rows(pg):
        lab, nums = T.split_row(r)
        toks = [t for _, _, t in r]
        if nums:
            print(f"  {lab[:44]:<46s} n={len(nums)} {nums}")
        else:
            print(f"  [text] {' '.join(toks)[:120]}")
