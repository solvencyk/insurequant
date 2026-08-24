# -*- coding: utf-8 -*-
"""PL 에는 있는데 CSM_waterfall 에는 **드문드문**한 회사를 센다 (read-only).

배경(2026-08-25): 휴리스틱 쳐내기의 커버리지 변이시험이 부산물로 잡아냈다 —
`하나생명보험` 은 PL_breakdown 에 14분기 전부 있는데 `CSM_waterfall` 에는 **2024.4Q 한 분기만**
있다. 그런데 완결성 census(`MASTER_HOLE`)는 조용하다. `coverage_holes(..., active_min=7)` 가
"활성 신고사" 문턱을 못 넘는 회사를 **struct(미공시)** 로 분류해 빼기 때문이다 —
즉 **적게 있을수록 검사에서 빠지는** 구조다.

이 스크립트는 그 형태를 전수로 센다. 판단은 안 한다(어떤 회사는 PAA 라 CSM 워터폴이
정말 없다) — **회사별 실데이터와 raw 유무만 제시**하고 판단은 parser/ifrs17 에 맡긴다.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

DISPLAY = ["2023.4Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"]


def load(fname):
    rows = json.loads((ROOT / fname).read_text(encoding="utf-8"))
    out = defaultdict(set)
    for r in rows:
        out[r["원수사명"]].add(r["공시분기"])
    return out


def raw_dirs(co: str) -> int:
    return len(list((ROOT / "data" / "dart").glob(f"FY*/raw/*{co}*")))


def main() -> int:
    wf, pl = load("CSM_waterfall.json"), load("PL_breakdown.json")
    all_q = sorted({q for s in pl.values() for q in s})
    print(f"PL 분기 {len(all_q)}개 · PL 회사 {len(pl)} · WF 회사 {len(wf)}\n")

    rows = []
    for co in sorted(pl):
        wq, pq = wf.get(co, set()), pl[co]
        wd = len(wq & set(DISPLAY))
        pd_ = len(pq & set(DISPLAY))
        if pd_ and wd < pd_:
            rows.append((co, len(wq), len(pq), wd, pd_, sorted(wq)))

    print(f"{'회사':22s} {'WF분기':>6s} {'PL분기':>6s} {'WF표시':>6s} {'PL표시':>6s} {'raw':>4s}  WF 보유분기")
    print("-" * 110)
    for co, nw, npl, wd, pd_, wq in sorted(rows, key=lambda r: (r[3], -r[4])):
        print(f"{co:22s} {nw:6d} {npl:6d} {wd:6d} {pd_:6d} {raw_dirs(co):4d}  "
              f"{','.join(wq) if wq else '(없음)'}")
    print(f"\nWF 가 PL 보다 적은 회사: {len(rows)}")
    print("  WF 표시분기 0    :", sum(1 for r in rows if r[3] == 0))
    print("  WF 표시분기 1-2  :", sum(1 for r in rows if 1 <= r[3] <= 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
