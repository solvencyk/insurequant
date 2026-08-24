# -*- coding: utf-8 -*-
"""'페이지 X / N' 스탬프로 page0(0-idx) <-> 인쇄쪽수 매핑을 만든다 (풀폼 문서에서 목표 섹션 위치 특정용)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]

STAMP_RE = re.compile(r"페이지\s*(\d+)\s*/\s*(\d+)")


def main():
    relpath = sys.argv[1]
    lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    hi = int(sys.argv[3]) if len(sys.argv) > 3 else None
    pdf = REPO / relpath
    doc = fitz.open(pdf)
    hi = hi if hi is not None else doc.page_count
    for p in range(lo, min(hi, doc.page_count)):
        t = doc[p].get_text()
        m = STAMP_RE.search(t)
        stamp = m.group(0) if m else "(no stamp)"
        print(f"page0={p:4d}  chars={len(t):5d}  {stamp}")
    doc.close()


if __name__ == "__main__":
    main()
