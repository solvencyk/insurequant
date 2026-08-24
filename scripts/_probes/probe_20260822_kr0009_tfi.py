# -*- coding: utf-8 -*-
"""probe_20260822_kr0009_tfi.py -- read-only investigation, KR0009 (Hyundai Marine) 2023.1Q.

Dumps the full PDF text (14 pages) to a sidecar file and searches for TFI
(transition/gyeong-gwa-jochi) table keywords individually per page, since the
combined 3-keyword search in fix_20260822_tfi_tier_full_scan.py::extract_tfi_full
found nothing. Pure investigation -- writes only to scripts/_probes/, never touches
kics_disclosure.json or any other repo file.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = REPO / "data" / "disclosure" / "FY2023_Q1" / "raw" / "KR0009_현대해상.pdf"
OUT_DIR = REPO / "scripts" / "_probes"

KEYWORDS = ["경과조치", "공통적용", "보완자본", "한도", "해약환급금", "지급여력기준금액",
            "지급여력금액", "기본자본", "선택적용", "적용에 관한 사항"]


def main():
    doc = fitz.open(PDF)
    n = doc.page_count
    page_texts = [doc[i].get_text() for i in range(n)]
    doc.close()

    print(f"PDF: {PDF.name}  pages={n}  size={PDF.stat().st_size:,} bytes")
    print()

    dump_path = OUT_DIR / "kr0009_2023q1_full_dump.txt"
    with dump_path.open("w", encoding="utf-8") as f:
        for i, t in enumerate(page_texts):
            f.write(f"\n{'='*80}\n=== PAGE idx={i} (1-based p{i+1}) === chars={len(t)}\n{'='*80}\n")
            f.write(t)
            f.write("\n")
    print(f"Full dump -> {dump_path}")
    print()

    print("=== Per-page char density ===")
    for i, t in enumerate(page_texts):
        print(f"  idx={i} (p{i+1}): {len(t)} chars")
    total = sum(len(t) for t in page_texts)
    print(f"  TOTAL={total} chars over {n} pages, avg={total/n:.1f}/page")
    print()

    print("=== Individual keyword occurrence by page (0-idx) ===")
    for kw in KEYWORDS:
        pages_found = [i for i, t in enumerate(page_texts) if kw in t]
        counts = {i: page_texts[i].count(kw) for i in pages_found}
        print(f"  '{kw}': pages={pages_found}  counts={counts}")
    print()

    matched = {i for i, t in enumerate(page_texts)
               if "공통적용" in t and "보완자본" in t and "한도" in t}
    print(f"3-keyword combo (공통적용+보완자본+한도) same-page: {sorted(matched)}")
    print()

    print("=== TOC / 목차 / 차례 candidates ===")
    found_toc = False
    for i, t in enumerate(page_texts):
        if "목차" in t or "차례" in t:
            found_toc = True
            print(f"  candidate idx={i} (p{i+1})")
    if not found_toc:
        print("  none found")


if __name__ == "__main__":
    raise SystemExit(main())
