# -*- coding: utf-8 -*-
"""One-off investigation for inbox ticket 20260821T1030Z F3 (page-continuation + dash
semantics). Read-only, prints diagnostics. Not part of the pipeline."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]


def dump_pages(pdf_path: Path, page_range):
    doc = fitz.open(pdf_path)
    try:
        for i in page_range:
            if i < 0 or i >= doc.page_count:
                continue
            text = doc[i].get_text()
            has_a = "경과조치" in text
            has_b = "기본요구자본" in text
            print(f"--- page idx={i} (p{i+1})  경과조치={has_a}  기본요구자본={has_b} ---")
            print(text[:1200])
            print()
    finally:
        doc.close()


def find_matches(pdf_path: Path):
    doc = fitz.open(pdf_path)
    try:
        matched = []
        for i in range(doc.page_count):
            text = doc[i].get_text()
            if "경과조치" in text and "기본요구자본" in text:
                matched.append(i)
        print(f"{pdf_path.name}: matched pages (0-idx) = {matched}  total_pages={doc.page_count}")
        return matched
    finally:
        doc.close()


if __name__ == "__main__":
    print("=== 1) 흥국화재 2023.1Q KR0005 — F3a page-continuation ===")
    p1 = REPO / "data/disclosure/FY2023_Q1/raw/KR0005_흥국화재_amended.pdf"
    m1 = find_matches(p1)
    # show a window around the matched pages to find the gap
    if m1:
        lo, hi = min(m1), max(m1)
        dump_pages(p1, range(max(0, lo - 1), min(hi + 2, 999)))

    print("\n\n=== 2) 롯데손해보험 2023.2Q — F3b dash semantics (need path) ===")
    for cand in (REPO / "data/disclosure/FY2023_Q2/raw").glob("*롯데*"):
        print(cand)
