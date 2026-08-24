# -*- coding: utf-8 -*-
"""Read-only: locate the K-ICS headline / TFI tables in the 5 target raw PDFs.

Prints per-page text density + hits for anchor strings, so we never conclude
"source absent" from a single keyword miss (repo trap: keyword absence != source absence).
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]

PDFS = [
    ("KR0003 2023.1Q", "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf"),
    ("KR0003 2024.4Q", "data/disclosure/FY2024_Q4/raw/KR0003_롯데손해보험.pdf"),
    ("KR0003 2025.1Q", "data/disclosure/FY2025_Q1/raw/KR0003_롯데손해보험.pdf"),
    ("KR0003 2026.1Q", "data/disclosure/FY2026_Q1/raw/KR0003_롯데손해보험.pdf"),
    ("KR0004 2025.1Q", "data/disclosure/FY2025_Q1/raw/KR0004_예별손해보험.pdf"),
]

ANCHORS = [
    "보완자본 한도",
    "한도 적용 전",
    "해약환급금",
    "지급여력비율의 경과조치",
    "기본자본",
    "보완자본으로 재분류",
    "지급여력금액으로 불인정",
    "건전성감독기준 재무상태표",
]


def main() -> None:
    for label, rel in PDFS:
        pdf = ROOT / rel
        print("=" * 100)
        print(f"{label}  {rel}")
        if not pdf.exists():
            print("   !! FILE MISSING")
            continue
        doc = fitz.open(pdf)
        print(f"   pages={len(doc)}")
        for i in range(len(doc)):
            t = doc[i].get_text("text")
            hits = [a for a in ANCHORS if a in t]
            if hits:
                print(f"   p{i+1:>3}  chars={len(t):>5}  hits={hits}")
        # density map for pages with no text at all
        empties = [i + 1 for i in range(len(doc)) if len(doc[i].get_text('text').strip()) < 40]
        if empties:
            print(f"   near-empty text pages (scan suspects): {empties}")
        doc.close()


if __name__ == "__main__":
    main()
