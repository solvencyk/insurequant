# -*- coding: utf-8 -*-
"""3·4·5번 파일에 걸 **의미 있는** 검사 후보를 실측으로 타당성 확인한다.

형식만 갖춘 검사(파일 존재 여부)는 금지 — 실제로 닫히는(또는 닫혀야 하는) 관계를 찾는다.

사용: python scripts/_probes/probe_20260825_design_viz_checks.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def j(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def wf_index():
    idx = defaultdict(dict)
    for r in j("CSM_waterfall.json"):
        idx[(r["원수사명"], r["공시분기"])][r["항목번호"]] = r["값"]
    return idx


def qkey(q):
    y, qq = q.split(".")
    return (int(y), int(qq[0]))


# ---------------------------------------------------------------- 3) amort
def check_amort():
    print("=" * 92)
    print("3) csm_amort_schedule.json")
    print("=" * 92)
    a = j("data/dart/viz/csm_amort_schedule.json")
    wf = wf_index()
    latest = {}
    for (co, q), items in wf.items():
        if items.get(6) is None:
            continue
        if co not in latest or qkey(q) > qkey(latest[co][0]):
            latest[co] = (q, items[6])

    st = defaultdict(int)
    for c in a["companies"]:
        st[c.get("status")] += 1
    print(f"  period={a['period']}  companies={len(a['companies'])}  status={dict(st)}")

    print("\n  (a) 내부 정합: yearly 합 vs total, buckets 합 vs total")
    bad_y = bad_b = 0
    for c in a["companies"]:
        y, b = c.get("yearly") or {}, c.get("buckets") or {}
        if y and y.get("total") is not None:
            s = sum(v for k, v in y.items() if k != "total" and isinstance(v, (int, float)))
            if abs(s - y["total"]) > max(1.0, 0.005 * abs(y["total"])):
                bad_y += 1
                if bad_y <= 6:
                    print(f"     YEARLY≠TOTAL {c['company']:20s} Σ={s:,.1f} total={y['total']:,.1f} "
                          f"Δ={s - y['total']:,.1f} ({(s / y['total'] - 1) * 100 if y['total'] else 0:+.1f}%)")
        if b and b.get("total") is not None:
            s = sum(v for k, v in b.items() if k != "total" and isinstance(v, (int, float)))
            if abs(s - b["total"]) > max(1.0, 0.005 * abs(b["total"])):
                bad_b += 1
                if bad_b <= 6:
                    print(f"     BUCKET≠TOTAL {c['company']:20s} Σ={s:,.1f} total={b['total']:,.1f} "
                          f"Δ={s - b['total']:,.1f}")
    print(f"     -> yearly 불일치 {bad_y}/{len(a['companies'])}, bucket 불일치 {bad_b}")

    print("\n  (b) total vs CSM_waterfall 기말CSM(최신분기, 억원)")
    hits = miss = 0
    ratios = []
    for c in a["companies"]:
        co = c["company"]
        tot = (c.get("yearly") or {}).get("total") or (c.get("buckets") or {}).get("total")
        if tot is None or co not in latest:
            miss += 1
            continue
        q, cl = latest[co]
        if not cl:
            continue
        ratios.append((abs(tot / cl) if cl else 0, co, q, tot, cl))
        hits += 1
    ratios.sort()
    print(f"     대조가능 {hits}건 / 대조불가 {miss}건")
    for r, co, q, tot, cl in ratios[:8]:
        print(f"     LOW  {co:22s} {q} amort_total={tot:>12,.1f} 기말CSM={cl:>12,.1f} ratio={r:.3f}")
    print("     ...")
    for r, co, q, tot, cl in ratios[-8:]:
        print(f"     HIGH {co:22s} {q} amort_total={tot:>12,.1f} 기말CSM={cl:>12,.1f} ratio={r:.3f}")
    within = sum(1 for r, *_ in ratios if 0.8 <= r <= 1.25)
    print(f"     -> ratio 0.8~1.25 안: {within}/{len(ratios)}")

    print("\n  (c) census: CSM_waterfall 에 있는데 amort 에 없는 회사")
    have = {c["company"] for c in a["companies"]}
    allco = {co for co, _ in wf}
    print(f"     wf companies={len(allco)}  amort companies={len(have)}")
    print(f"     amort 결측: {sorted(allco - have)}")
    print(f"     wf 에 없는 amort 회사: {sorted(have - allco)}")


# ---------------------------------------------------------------- 4) history
def check_history():
    print("\n" + "=" * 92)
    print("4) csm_waterfall_history.json  (정적 스냅샷 — 마스터와의 drift 규모 측정)")
    print("=" * 92)
    h = j("data/dart/viz/csm_waterfall_history.json")
    wf = wf_index()
    STAGE2ITEM = {"opening": 1, "new_business": 2, "interest": 3,
                  "assumption": 4, "amortization": 5, "closing": 6}
    ident_fail = ident_pass = ident_skip = 0
    fails = []
    drift = []
    n_cells = n_match = 0
    missing_in_master = []
    for c in h["companies"]:
        co = c["company"]
        for q, p in c["periods"].items():
            stg = p.get("stages") or {}
            vals = {k: (stg.get(k) or {}).get("value_mn_krw") for k in STAGE2ITEM}
            if all(vals[k] is not None for k in STAGE2ITEM):
                lhs = vals["closing"]
                rhs = sum(vals[k] for k in
                          ("opening", "new_business", "interest", "assumption", "amortization"))
                tol = max(1.0, 0.001 * abs(lhs))
                if abs(lhs - rhs) > tol:
                    ident_fail += 1
                    fails.append((co, q, lhs, rhs, lhs - rhs))
                else:
                    ident_pass += 1
            else:
                ident_skip += 1
            # 마스터 대조: history=백만원, master=억원 -> /100
            m = wf.get((co, q))
            if m is None:
                missing_in_master.append((co, q))
                continue
            for k, it in STAGE2ITEM.items():
                hv, mv = vals[k], m.get(it)
                if hv is None or mv is None:
                    continue
                n_cells += 1
                a_, b_ = hv / 100.0, mv
                tol = max(2.0, 0.01 * abs(b_))
                if abs(a_ - b_) <= tol:
                    n_match += 1
                else:
                    drift.append((co, q, k, a_, b_, a_ - b_))
    print(f"  회사={len(h['companies'])} periods={len(h['periods'])}")
    print(f"  (a) 단계 항등식 opening+nb+int+assum+amort=closing : pass={ident_pass} "
          f"fail={ident_fail} skip={ident_skip}")
    for x in fails[:10]:
        print(f"      FAIL {x[0]:20s} {x[1]} closing={x[2]:,.0f} Σ={x[3]:,.0f} Δ={x[4]:,.0f}")
    print(f"\n  (b) 마스터(CSM_waterfall) 대조 셀 {n_cells} 중 일치 {n_match} / drift {len(drift)}"
          f"  ({len(drift) / n_cells * 100 if n_cells else 0:.1f}%)")
    drift.sort(key=lambda x: -abs(x[5]))
    for x in drift[:12]:
        print(f"      DRIFT {x[0]:20s} {x[1]} {x[2]:13s} hist={x[3]:>12,.1f} master={x[4]:>12,.1f} "
              f"Δ={x[5]:>+12,.1f}")
    print(f"\n  (c) history 에 있는데 마스터에 없는 (회사,분기): {len(missing_in_master)}")
    print(f"      {missing_in_master[:10]}")
    allco = {co for co, _ in wf}
    hco = {c["company"] for c in h["companies"]}
    print(f"  (d) 마스터에 있는데 history 에 없는 회사 {len(allco - hco)}: {sorted(allco - hco)}")


# ---------------------------------------------------------------- 5) ins pl
def _num(s):
    if s is None:
        return None
    s = str(s).strip().replace(",", "").replace(" ", "")
    if s in ("", "-", "–", "—"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace("△", "-").replace("▲", "-")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def check_ins_pl():
    print("\n" + "=" * 92)
    print("5) insurance_pl_breakdown.json")
    print("=" * 92)
    p = j("data/dart/viz/insurance_pl_breakdown.json")
    st = defaultdict(int)
    for c in p["companies"]:
        st[c.get("status")] += 1
    print(f"  period={p['period']}  companies={len(p['companies'])}  status={dict(st)}")

    print("\n  (a) 각 표의 행 라벨 분포 (대조 후보 행 찾기)")
    labs = defaultdict(int)
    for c in p["companies"]:
        for row in (c.get("table") or []):
            if row:
                labs[re.sub(r"\s+", "", str(row[0]))] += 1
    for lab, n in sorted(labs.items(), key=lambda x: -x[1])[:22]:
        print(f"     {n:3d}  {lab}")

    print("\n  (b) 행 내부 산수: 마지막 열(합계) == 앞 숫자열 합?")
    ok = bad = skip = 0
    bads = []
    for c in p["companies"]:
        for row in (c.get("table") or []):
            nums = [_num(x) for x in row[1:]]
            if len(nums) < 3 or any(x is None for x in nums):
                skip += 1
                continue
            *parts, tot = nums
            s = sum(parts)
            if abs(s - tot) <= max(1.0, 0.01 * abs(tot)):
                ok += 1
            else:
                bad += 1
                if len(bads) < 8:
                    bads.append((c["company"], re.sub(r"\s+", "", str(row[0])), s, tot))
    print(f"     row-sum pass={ok} fail={bad} skip={skip}")
    for x in bads:
        print(f"     ROWSUM {x[0]:20s} {x[1]:26s} Σ={x[2]:>14,.0f} 합계={x[3]:>14,.0f}")

    print("\n  (c) census: PL_breakdown 마스터 대비")
    plco = {r["원수사명"] for r in j("PL_breakdown.json")}
    have = {c["company"] for c in p["companies"]}
    print(f"     PL master companies={len(plco)}  ins_pl companies={len(have)}")
    print(f"     ins_pl 결측: {sorted(plco - have)}")
    print(f"     master 에 없는 ins_pl 회사: {sorted(have - plco)}")


def main() -> int:
    check_amort()
    check_history()
    check_ins_pl()
    return 0


if __name__ == "__main__":
    sys.exit(main())
