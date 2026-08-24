# -*- coding: utf-8 -*-
"""KB손해(KR0010) 전 분기 item1/14/15/16/17/18/19/20/21/22/27/28 전후 마스터 현황 +
2025.1Q raw 페이지별 텍스트밀도."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MASTER = REPO / "kics_disclosure.json"


def main() -> int:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    by_cq: dict = {}
    for r in rows:
        c, q = r["원보험사코드"], r["공시분기"]
        if c == "KR0010":
            by_cq.setdefault(q, {})[int(r["항목번호"])] = r

    print("=== KR0010 KB손해보험 전분기 현황 (item: 전 | 후) ===")
    for q in sorted(by_cq):
        items = by_cq[q]
        line = f"{q}: "
        for it in (1, 14, 15, 17, 18, 19, 20, 21, 27, 28):
            row = items.get(it)
            if row is None:
                line += f"[{it}:없음] "
            else:
                line += f"[{it}:{row.get('값')}|{row.get('값_적용후','-')}] "
        print(line)

    print("\n=== 2025.1Q raw 페이지별 텍스트밀도 ===")
    raw = REPO / "data" / "disclosure" / "FY2025_Q1" / "raw"
    pdfs = sorted(raw.glob("KR0010_*.pdf"))
    pdf = max(pdfs, key=lambda p: p.stat().st_size)
    print(f"pdf={pdf}  size={pdf.stat().st_size:,}")
    doc = fitz.open(pdf)
    try:
        print(f"page_count={doc.page_count}")
        for i in range(doc.page_count):
            t = doc[i].get_text()
            if len(t.strip()) > 0:
                print(f"  p{i} (1-idx {i+1}): {len(t)}자  repr={t.strip()[:80]!r}")
    finally:
        doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
