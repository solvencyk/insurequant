# -*- coding: utf-8 -*-
"""동양생명(KR0087)·케이디비생명보험(KR0072) PL_breakdown 루트 item1~12 덤프.

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_dy_kdb_full_items.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

ITEM_NM = {1: "보험손익", 2: "생명장기손익", 3: "생명장기원수손익", 4: "원수CSM상각",
           5: "원수위험조정변동", 6: "원수예실차", 7: "기타생명장기원수손익",
           8: "생명장기재보험손익", 9: "재보험CSM상각", 10: "재보험위험조정변동",
           11: "재보험예실차", 12: "기타생명장기재보험손익"}

TARGETS = {"KR0087": ["2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"],
           "KR0072": ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]}


def main() -> int:
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    by_code_q = defaultdict(dict)
    for r in rows:
        by_code_q[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r.get("값")
    for code, qs in TARGETS.items():
        for q in qs:
            m = by_code_q.get((code, q), {})
            if not m:
                print(f"\n[{code} {q}] NO DATA")
                continue
            print(f"\n[{code} {q}]")
            for i in range(1, 13):
                print(f"  item{i:<2d} {ITEM_NM[i]:16s} = {m.get(i)}")
            i3, i4, i5, i6, i7 = m.get(3), m.get(4), m.get(5), m.get(6), m.get(7)
            if None not in (i3, i4, i5, i6, i7):
                rhs = i4 + i5 + i6 + i7
                print(f"  -> LHS(item3)={i3:,.6f}  RHS(4+5+6+7)={rhs:,.6f}  diff={rhs-i3:,.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
