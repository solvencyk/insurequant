# -*- coding: utf-8 -*-
"""NB_CSM_multiple.json (배포본) 에 걸 검사 후보 실측.

축:
  (a) 비율 항등식  배수 = CSM / 월납월초보험료   — 연누계 · 당분기 **둘 다**
  (b) 당분기 = 연누계(Q) - 연누계(Q-1)          (1Q 는 당분기 == 연누계)
  (c) 마스터 대조  신계약CSM_연누계 vs CSM_waterfall 항목2(신계약CSM)
  (d) census       마스터 (회사×분기) 그리드 대비 결측

사용: python scripts/_probes/probe_20260825_design_nb_checks.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def j(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def qkey(q):
    y, qq = q.split(".")
    return (int(y), int(qq[0]))


def prev_q(q):
    y, n = qkey(q)
    return None if n == 1 else f"{y}.{n - 1}Q"


def main() -> int:
    nb = j("NB_CSM_multiple.json")
    idx = {(r["원보험사코드"], r["공시분기"]): r for r in nb}

    print("=" * 92)
    print("(a) 비율 항등식  배수 = CSM / 월납월초보험료  (연누계 · 당분기 둘 다)")
    print("=" * 92)
    for axis in ("연누계", "당분기"):
        p = f = s = 0
        worst = []
        for r in nb:
            c = r.get(f"신계약CSM_{axis}")
            prem = r.get(f"월납월초보험료_{axis}")
            m = r.get(f"신계약CSM배수_{axis}")
            if c is None or prem is None or m is None or prem == 0:
                s += 1
                continue
            exp = c / prem
            tol = max(0.01, 0.005 * abs(exp))
            if abs(exp - m) <= tol:
                p += 1
            else:
                f += 1
                worst.append((abs(exp - m), r["원수사명"], r["공시분기"], c, prem, m, exp))
        worst.sort(reverse=True)
        print(f"  [{axis}] pass={p} fail={f} skip={s}")
        for d, co, q, c, prem, m, exp in worst[:8]:
            print(f"     FAIL {co:22s} {q} CSM={c:>11,.1f} prem={prem:>10,.4f} "
                  f"배수={m:>8,.4f} 계산={exp:>8,.4f} Δ={exp - m:+.4f}")

    print("\n" + "=" * 92)
    print("(b) 당분기 = 연누계(Q) - 연누계(Q-1)")
    print("=" * 92)
    for field in ("신계약CSM", "월납월초보험료"):
        p = f = s = 0
        worst = []
        for r in nb:
            q = r["공시분기"]
            cur = r.get(f"{field}_당분기")
            ytd = r.get(f"{field}_연누계")
            if cur is None or ytd is None:
                s += 1
                continue
            pq = prev_q(q)
            if pq is None:
                exp = ytd
            else:
                pr = idx.get((r["원보험사코드"], pq))
                if pr is None or pr.get(f"{field}_연누계") is None:
                    s += 1
                    continue
                exp = ytd - pr[f"{field}_연누계"]
            tol = max(0.5, 0.01 * abs(exp))
            if abs(exp - cur) <= tol:
                p += 1
            else:
                f += 1
                worst.append((abs(exp - cur), r["원수사명"], q, cur, exp))
        worst.sort(reverse=True)
        print(f"  [{field}] pass={p} fail={f} skip={s}")
        for d, co, q, cur, exp in worst[:6]:
            print(f"     FAIL {co:22s} {q} 당분기={cur:>12,.2f} 기대(YTD차)={exp:>12,.2f} Δ={cur - exp:+,.2f}")

    print("\n" + "=" * 92)
    print("(c) 신계약CSM_연누계 vs CSM_waterfall 항목2(신계약CSM)  — 단위/스케일")
    print("=" * 92)
    wf = defaultdict(dict)
    for r in j("CSM_waterfall.json"):
        wf[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r["값"]
    p = f = s = 0
    worst = []
    for r in nb:
        k = (r["원보험사코드"], r["공시분기"])
        a = r.get("신계약CSM_연누계")
        b = wf.get(k, {}).get(2)
        if a is None or b is None:
            s += 1
            continue
        tol = max(1.0, 0.01 * abs(b))
        if abs(a - b) <= tol:
            p += 1
        else:
            f += 1
            worst.append((abs(a - b), r["원수사명"], r["공시분기"], a, b))
    worst.sort(reverse=True)
    print(f"  pass={p} fail={f} skip={s}")
    for d, co, q, a, b in worst[:12]:
        print(f"     FAIL {co:22s} {q} NB={a:>12,.1f} wf항목2={b:>12,.1f} Δ={a - b:>+12,.1f} "
              f"ratio={a / b if b else float('nan'):.3f}")

    print("\n" + "=" * 92)
    print("(d) census — CSM_waterfall 그리드 대비 NB 결측")
    print("=" * 92)
    wf_keys = {k for k, v in wf.items() if v.get(2) is not None}
    nb_keys = set(idx)
    miss = sorted(wf_keys - nb_keys)
    extra = sorted(nb_keys - wf_keys)
    print(f"  wf(신계약CSM 존재) 셀={len(wf_keys)}  NB 행={len(nb_keys)}")
    print(f"  NB 에 없는 (회사,분기) {len(miss)}:")
    bycomp = defaultdict(list)
    for c, q in miss:
        bycomp[c].append(q)
    for c, qs in sorted(bycomp.items()):
        print(f"     {c}: {sorted(qs, key=qkey)}")
    print(f"  wf 에 없는 NB 행 {len(extra)}: {extra[:20]}")

    print("\n  null 셀 분포(배포본 안):")
    for k in ("신계약CSM_연누계", "월납월초보험료_연누계", "신계약CSM배수_연누계",
              "신계약CSM_당분기", "월납월초보험료_당분기", "신계약CSM배수_당분기"):
        nulls = [(r["원수사명"], r["공시분기"]) for r in nb if r.get(k) is None]
        print(f"    {k:24s} null={len(nulls):3d}  {nulls[:6]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
