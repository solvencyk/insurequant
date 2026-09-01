# -*- coding: utf-8 -*-
"""Verify KR0010/KR0079/KR0087 are genuinely image/scan (near-zero text
density) on their market-risk pages, vs KR0080/KR0082/KR0094/KR0099/KR0104
which should have real text (candidates for reconversion)."""
from __future__ import annotations
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz  # noqa: E402

PDF_DIR = REPO / "data" / "disclosure" / "FY2026_Q2" / "pdf"

CODES = {
    "KR0010": "KB손해보험(known scan?)",
    "KR0079": "미래에셋생명보험(known mixed?)",
    "KR0087": "동양생명(known scan?)",
    "KR0080": "AIA생명(reconvert candidate)",
    "KR0082": "DB생명보험(reconvert candidate)",
    "KR0094": "신한라이프(reconvert candidate)",
    "KR0099": "KB라이프생명(reconvert candidate)",
    "KR0104": "농협생명보험(reconvert candidate)",
}

for code, label in CODES.items():
    g = list(PDF_DIR.glob(f"{code}_*.pdf"))
    if not g:
        print(f"{code}: NO PDF")
        continue
    doc = fitz.open(g[0])
    total_pages = doc.page_count
    densities = []
    hit_pages = []
    for i in range(total_pages):
        t = doc[i].get_text()
        densities.append(len(t))
        if any(kw in t for kw in ("금리위험액", "주식위험액", "부동산위험액", "외환위험액", "자산집중위험액")):
            hit_pages.append((i + 1, len(t)))
    avg_density = sum(densities) / len(densities) if densities else 0
    print(f"{code} {label}: pages={total_pages} avg_chars/page={avg_density:.0f}")
    print(f"  market-risk keyword hit pages (1-based) + char count: {hit_pages}")
    doc.close()
