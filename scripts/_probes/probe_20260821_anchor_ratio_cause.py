# -*- coding: utf-8 -*-
"""'비율이상' 버킷 원인 확인: 에이비엘 2023.4Q raw에서 '기본요구자본' 이 어느 페이지·어떤
문맥에서 잡히는지 직접 덤프한다 (scan_occurrences 가 무엇을 오매칭했는지)."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGETS = [
    ("FY2023_Q4", "KR0070"),
    ("FY2023_Q1", "KR0073"),
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
        print(f"{period} {code}  {pdf.name}")
        doc = fitz.open(pdf)
        try:
            matched = {i for i in range(doc.page_count)
                       if "경과조치" in doc[i].get_text() and "기본요구자본" in doc[i].get_text()}
            print(f"  matched pages(경과조치+기본요구자본): {sorted(matched)}")
            for i in sorted(matched):
                text = doc[i].get_text()
                # 기본요구자본 근방 60자 출력
                idx = 0
                while True:
                    idx = text.find("기본요구자본", idx)
                    if idx < 0:
                        break
                    print(f"    p{i} @ {idx}: ...{text[max(0,idx-20):idx+80]!r}...")
                    idx += 5
        finally:
            doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
