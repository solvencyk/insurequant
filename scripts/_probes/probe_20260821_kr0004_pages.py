# -*- coding: utf-8 -*-
"""KR0004 예별손해보험 2023.4Q/2024.1Q/2024.2Q 원문에서 '금리위험' 이 언급된 모든 페이지를
전문 덤프한다 (scan_occurrences 의 page-inclusion 휴리스틱과 독립적으로 원문 직접 확인).
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGETS = [
    ("FY2023_Q4", "KR0004"),
    ("FY2024_Q1", "KR0004"),
    ("FY2024_Q2", "KR0004"),
]


def main() -> int:
    for period, code in TARGETS:
        raw = REPO / "data" / "disclosure" / period / "raw"
        pdfs = sorted(raw.glob(f"{code}_*.pdf"))
        if not pdfs:
            print(f"{period} {code}: raw 없음")
            continue
        pdf = max(pdfs, key=lambda p: p.stat().st_size)
        print("=" * 100)
        print(f"{period} {code}  {pdf.name}  ({pdf.stat().st_size:,} bytes)")
        doc = fitz.open(pdf)
        try:
            hits = []
            for i in range(doc.page_count):
                text = doc[i].get_text()
                if "금리위험" in text:
                    hits.append(i)
            print(f"  '금리위험' 언급 페이지(0-idx): {hits}")
            for i in hits:
                text = doc[i].get_text()
                print(f"  --- page {i} (1-idx {i+1}) ---")
                print(text)
        finally:
            doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
