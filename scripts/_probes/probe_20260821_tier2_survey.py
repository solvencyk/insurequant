# -*- coding: utf-8 -*-
"""tier2 한도 3줄 표(1) 공통적용 경과조치) 를 여러 회사에서 원문 그대로 덤프해 라벨
줄바꿈 패턴을 확인한다 (전용 추출기 작성 전 사전조사)."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGETS = [
    ("FY2026_Q1", "KR0083"),   # 푸본현대
    ("FY2026_Q1", "KR1011"),   # IBK연금
    ("FY2025_Q1", "KR0104"),   # 농협생명
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
            hits = [i for i in range(doc.page_count) if "보완자본" in doc[i].get_text() and "한도" in doc[i].get_text()]
            print(f"  '보완자본'+'한도' 페이지: {hits}")
            for i in hits:
                print(f"  --- page {i} (1-idx {i+1}) ---")
                print(doc[i].get_text())
        finally:
            doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
