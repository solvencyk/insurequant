#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find the page of the '8-1. 재무상태표' heading in the raw disclosure PDFs of a company (read-only).  usage: bspl_apply_findpage.py KR1105 [keyword]"""
import sys
from pathlib import Path

import fitz

from _disclosure_pdf_paths import disclosure_pdfs

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
code = sys.argv[1]
kw = sys.argv[2] if len(sys.argv) > 2 else "8-1.재무상태표"
for y in (2023, 2024, 2025, 2026):
    for n in (1, 2, 3, 4):
        for p in disclosure_pdfs(f"FY{y}_Q{n}", code):
            try:
                doc = fitz.open(str(p))
            except Exception as e:
                print(f"{y}.{n}Q {p.name}: cannot open {e}")
                continue
            hits = []
            for i in range(len(doc)):
                t = "".join(doc[i].get_text().split())
                if kw in t:
                    hits.append(i + 1)
            print(f"{y}.{n}Q {p.name[:40]:<40} pages={len(doc):>3} '{kw}' on {hits}")
