# -*- coding: utf-8 -*-
"""Step 61 (read-only probe): why does the reader miss one row on the FY2024_Q1..Q3 roll-forward pages, and what do they open with?"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lina_tbl as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)

for fy, p in (("FY2024_Q1", 51), ("FY2024_Q3", 52)):
    pdf = sorted((ROOT / "data" / "disclosure" / fy / "raw").glob("KR0074_*.pdf"))[0]
    pg = fitz.open(pdf)[p - 1]
    print(f"\n=== {fy} p{p}")
    for r in T.page_rows(pg):
        lab, nums = T.split_row(r)
        if nums:
            print(f"  {lab[:40]:<42s} {nums}")
