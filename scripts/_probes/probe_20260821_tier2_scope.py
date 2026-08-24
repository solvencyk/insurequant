# -*- coding: utf-8 -*-
"""tier2 스코프 확정: 마스터의 전체 (회사,분기) 목록과 raw PDF 존재여부를 나열."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MASTER = REPO / "kics_disclosure.json"
DISCLOSURE = REPO / "data" / "disclosure"


def q2p(q):
    y, qq = q.split(".")
    return f"FY{y}_Q{qq[0]}"


def main() -> int:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    by_c: dict[str, set] = {}
    name = {}
    for r in rows:
        c, q = r["원보험사코드"], r["공시분기"]
        name[c] = r.get("원수사명", c)
        by_c.setdefault(c, set()).add(q)

    total_cq = 0
    total_raw = 0
    for c in sorted(by_c):
        qs = sorted(by_c[c])
        has_raw = 0
        for q in qs:
            raw = DISCLOSURE / q2p(q) / "raw"
            pdfs = list(raw.glob(f"{c}_*.pdf")) if raw.exists() else []
            if pdfs:
                has_raw += 1
        total_cq += len(qs)
        total_raw += has_raw
        print(f"{c} {name[c]:<16} 분기수={len(qs):>2} raw존재={has_raw:>2}  {qs}")
    print(f"\n합계: 회사수={len(by_c)}  (회사,분기)={total_cq}  raw존재={total_raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
