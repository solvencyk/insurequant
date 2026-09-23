# -*- coding: utf-8 -*-
"""forward 재산출 전/후 차이가 '콜 지난 미상환분' 으로 정확히 설명되는지 검산한다.

기대: 회사·연도별 차감액 감소분 == 그 회사의 콜 지난 미상환 채권들이
      `기준시점 인정액 - 연도말 인정액` 대신 전액 차감당하던 몫.
설명 안 되는 회사·연도가 하나라도 있으면 산식이 의도 밖으로 샌 것이다.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.build_capital_securities_recognition import tier2_recognition_rate  # noqa: E402

BEFORE = Path(sys.argv[1])
AS_OF = date(2026, 6, 30)
bonds = json.loads((REPO / "data/bonds/capital_securities_fy2026h1.json").read_text(encoding="utf-8"))


def pd(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None


# 회사별 '콜 지난 미상환' 채권
past = {}
for c in bonds["companies"]:
    for b in c.get("bonds") or []:
        if (b.get("outstanding_mn") or 0) <= 0:
            continue
        call, legal = pd(b.get("call_date")), pd(b.get("legal_maturity"))
        if call and call <= AS_OF and legal:
            past.setdefault(c["code"], []).append(
                {"amt": b["outstanding_mn"] / 100.0, "legal": legal, "name": b["name"][:30]})

bf = {r["insurer_code"]: r for r in json.loads(BEFORE.read_text(encoding="utf-8"))}
af = {r["insurer_code"]: r for r in json.loads((REPO / "kics_forward_capital.json").read_text(encoding="utf-8"))}

bad, checked = [], 0
for code, ra in af.items():
    rb = bf.get(code)
    if not rb or ra.get("status") != "ok" or rb.get("status") != "ok":
        continue
    pbs = {p["year"]: p for p in rb["projections"]}
    for p in ra["projections"]:
        q = pbs.get(p["year"])
        if not q:
            continue
        checked += 1
        got = q["cumulative_bond_dedu_eok"] - p["cumulative_bond_dedu_eok"]   # 차감이 줄어든 몫
        ye = date(p["year"], 12, 31)
        exp = 0.0
        for x in past.get(code, []):
            r_as_of = tier2_recognition_rate({"legal_maturity": x["legal"].isoformat()}, AS_OF)
            r_ye = tier2_recognition_rate({"legal_maturity": x["legal"].isoformat()}, ye)
            exp += x["amt"] - x["amt"] * (r_as_of - r_ye)     # 전액차감 -> 증분차감
        if abs(got - exp) > 0.15:
            bad.append((ra["insurer_name"], p["year"], got, exp))

print(f"대조 {checked} (회사,연도) · 설명 안 되는 건 {len(bad)}")
for r in bad[:20]:
    print(f"  {r[0]} {r[1]}: 실제감소 {r[2]:,.1f} vs 기대 {r[3]:,.1f}")
n = sum(1 for c, ra in af.items() for p in ra.get("projections", [])
        if (p.get("ratio_pct") or 0) != ((bf.get(c) or {}).get("projections") and
            next((q["ratio_pct"] for q in bf[c]["projections"] if q["year"] == p["year"]), None)))
print(f"비율이 바뀐 (회사,연도): {n}")
