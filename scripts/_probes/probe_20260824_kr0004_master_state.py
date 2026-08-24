# -*- coding: utf-8 -*-
"""KR0004 3개 분기의 item19·36-40 마스터 현재 저장값을 raw 인쇄값과 나란히 찍는다 (read-only).

목적: item36후=0.00 이 실제로 '고립된 결측'인지, 아니면 item19후(부모)·37-40후(형제)는
이미 raw와 정확히 일치하고 item36후 한 칸만 비어 있는지 확인한다.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MASTER = REPO / "kics_disclosure.json"

# raw 인쇄값 (백만원), probe_20260821_kr0004_pages.py 원문 덤프에서 직접 옮김
RAW = {
    "2023.4Q": {19: (213547, 110677), 36: (65239, None), 37: (188325, 112644),
                38: (3923, 3923), 39: (19238, 19238), 40: (None, None)},
    "2024.1Q": {19: (215769, 116622), 36: (71606, None), 37: (187085, 118972),
                38: (3524, 3524), 39: (21282, 21282), 40: (None, None)},
    "2024.2Q": {19: (224367, 134130), 36: (56790, None), 37: (204164, 136050),
                38: (3916, 3916), 39: (15982, 15982), 40: (None, None)},
}

rows = json.loads(MASTER.read_text(encoding="utf-8"))
by_cq: dict = {}
for r in rows:
    if r["원보험사코드"] != "KR0004":
        continue
    by_cq.setdefault(r["공시분기"], {})[int(r["항목번호"])] = r

for q in ("2023.4Q", "2024.1Q", "2024.2Q"):
    items = by_cq.get(q, {})
    print(f"=== KR0004 {q} ===")
    for it in (19, 36, 37, 38, 39, 40):
        row = items.get(it)
        pre_raw, post_raw = RAW[q][it]
        pre_m = row.get("값") if row else None
        post_m = row.get("값_적용후") if row else None
        pre_expect = "" if pre_raw is None else f"{pre_raw/100:,.2f}"
        post_expect = "-(대시)" if post_raw is None else f"{post_raw/100:,.2f}"
        print(f"  item{it:<3} raw전={pre_raw!s:>8} raw후={post_raw!s:>8}  "
              f"| 마스터전={pre_m!s:>10}(기대{pre_expect:>10})  마스터후={post_m!s:>10}(기대 {post_expect})")
