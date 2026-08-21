# -*- coding: utf-8 -*-
"""F3b dash-semantics check: does the 경과조치 적용후 column show '-' for market-risk leaves
when the company doesn't apply that selective transition (mirror = unchanged), and is '전' non-zero
in that same row? Read-only diagnostic."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]


def dump(pdf_path: Path, keyword_a="경과조치", keyword_b="기본요구자본", context=1):
    doc = fitz.open(pdf_path)
    try:
        matched = [i for i in range(doc.page_count)
                   if keyword_a in doc[i].get_text() and keyword_b in doc[i].get_text()]
        print(f"{pdf_path.name}: matched={matched} total={doc.page_count}")
        shown = set()
        for i in matched:
            for j in range(max(0, i - context), min(doc.page_count, i + context + 1)):
                shown.add(j)
        for i in sorted(shown):
            print(f"--- page idx={i} (p{i+1}) ---")
            print(doc[i].get_text())
    finally:
        doc.close()


if __name__ == "__main__":
    for p in [
        REPO / "data/disclosure/FY2023_Q2/raw/KR0003_롯데손해보험.pdf",
    ]:
        dump(p)
        print("=" * 80)
