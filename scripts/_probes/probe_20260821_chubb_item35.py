# -*- coding: utf-8 -*-
"""처브라이프(KR0100) 2024.4Q raw에서 '대재해위험' 이 언급된 모든 페이지를 전문 덤프
(46.81 vs 44.99 중 어느 쪽이 맞는지 원문 직접 확인)."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main() -> int:
    raw = REPO / "data" / "disclosure" / "FY2024_Q4" / "raw"
    pdfs = sorted(raw.glob("KR0100_*.pdf"))
    pdf = max(pdfs, key=lambda p: p.stat().st_size)
    print(f"{pdf}  ({pdf.stat().st_size:,} bytes)")
    doc = fitz.open(pdf)
    try:
        hits = [i for i in range(doc.page_count) if "대재해위험" in doc[i].get_text()]
        print(f"'대재해위험' 언급 페이지(0-idx): {hits}  / 총 {doc.page_count}p")
        for i in hits:
            print(f"--- page {i} (1-idx {i+1}) ---")
            print(doc[i].get_text())
    finally:
        doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
