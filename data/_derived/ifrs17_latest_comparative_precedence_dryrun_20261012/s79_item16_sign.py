"""Read-only: item 15/16 (기타영업수익 / 기타사업비용) values and sign convention per quarter for a few non-life companies (master) + bridge residuals"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
M = {}
for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8")):
    M[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r["값"]
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025) for q in (1, 2, 3, 4)] + ["2026.1Q"]
for kr in sys.argv[1:]:
    print("=" * 100, kr)
    for q in QS:
        v = {i: M.get((kr, q, i)) for i in (1, 2, 13, 14, 15, 16)}
        if v[1] is None and v[2] is None:
            continue
        legs = [v[2], v[13], v[14]]
        if None in legs or v[1] is None:
            print(q, v, "(incomplete)")
            continue
        bare = sum(legs)
        a1 = bare + (v[15] or 0) - (v[16] or 0)
        a2 = bare + (v[15] or 0) + (v[16] or 0)
        print(q, {k: (round(x, 1) if x is not None else None) for k, x in v.items()}, " res(bare)=%.1f res(15-16)=%.1f res(15+16)=%.1f" % (v[1] - bare, v[1] - a1, v[1] - a2))
