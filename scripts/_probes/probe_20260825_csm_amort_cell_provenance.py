# -*- coding: utf-8 -*-
"""원수CSM상각 셀이 배포본과 viz 에서 갈린 8건 — 어느 쪽이 맞나.

가설 A: 배포본이 stale (viz 가 파서 정정 후 최신)
가설 B: 배포본이 YTD 누계, viz 가 당분기 (basis mix)
가설 C: 단위 불일치

각 회사의 전 분기 시계열을 나란히 찍어 판별한다. 항등식 잔차도 같이 본다.

사용: python scripts/_probes/probe_20260825_csm_amort_cell_provenance.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIZ = ROOT / "data" / "dart" / "viz" / "pl_breakdown_master.json"
DEP = ROOT / "PL_breakdown.json"

TARGETS = ["동양생명", "에이비엘생명보험", "케이디비생명보험"]
ITEM = "원수CSM상각"
IDENT = [("생명장기원수손익", 1), ("원수CSM상각", -1), ("원수위험조정변동", -1),
         ("원수예실차", -1), ("기타생명장기원수손익", -1)]


def load(p: Path):
    rows = json.loads(p.read_text(encoding="utf-8"))
    idx = defaultdict(dict)
    meta = {}
    for r in rows:
        k = (r["원수사명"], r["공시분기"])
        idx[k][(r["항목명"] or "").replace(" ", "")] = r["값"]
        if (r["항목명"] or "").replace(" ", "") == ITEM:
            meta[k] = {x: r.get(x) for x in r
                       if x not in ("값", "항목명", "원수사명", "공시분기")}
    return idx, meta


def qkey(q):
    y, qq = q.split(".")
    return (int(y), int(qq[0]))


def main() -> int:
    v, vm = load(VIZ)
    d, dm = load(DEP)
    for co in TARGETS:
        qs = sorted({q for (c, q) in set(v) | set(d) if c == co}, key=qkey)
        print("\n" + "=" * 96)
        print(f"[{co}]  {ITEM}  (백만원)")
        print("=" * 96)
        print(f"  {'분기':9s} {'viz':>13s} {'배포본':>13s} {'배포-viz':>13s} "
              f"{'viz증분':>11s} {'dep증분':>11s} | {'항등식잔차(viz)':>15s} {'항등식잔차(dep)':>15s}")
        pv = pd = None
        for q in qs:
            a = v.get((co, q), {}).get(ITEM)
            b = d.get((co, q), {}).get(ITEM)
            iv = (a - pv) if (a is not None and pv is not None) else None
            idp = (b - pd) if (b is not None and pd is not None) else None
            if q.endswith("1Q"):
                iv = idp = None
            rv = rd = None
            cv, cd = v.get((co, q), {}), d.get((co, q), {})
            if all(cv.get(k) is not None for k, _ in IDENT):
                rv = sum(s * cv[k] for k, s in IDENT)
            if all(cd.get(k) is not None for k, _ in IDENT):
                rd = sum(s * cd[k] for k, s in IDENT)
            f = lambda x: "-" if x is None else f"{x:,.1f}"
            print(f"  {q:9s} {f(a):>13s} {f(b):>13s} "
                  f"{f(None if (a is None or b is None) else b - a):>13s} "
                  f"{f(iv):>11s} {f(idp):>11s} | {f(rv):>15s} {f(rd):>15s}")
            pv, pd = (a if a is not None else pv), (b if b is not None else pd)
        # 셀 메타(출처/노트)
        for q in qs[:3]:
            if (co, q) in vm or (co, q) in dm:
                print(f"    meta[{q}] viz={vm.get((co, q))}")
                print(f"    meta[{q}] dep={dm.get((co, q))}")
                break
    return 0


if __name__ == "__main__":
    sys.exit(main())
