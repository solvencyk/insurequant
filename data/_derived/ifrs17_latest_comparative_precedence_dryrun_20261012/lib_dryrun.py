"""Shared read-only helpers of the IFRS17 latest-comparative-precedence dry run (ticket 20261012T1930Z).

* masters loaded from the repo root (never written)
* STRICT CSM closure rules - the same arithmetic as scripts/validate_master_tables._check_plausibility / validate_csm_continuity,
  but WITHOUT the documented-exception sets (an exception documents a break; it does not close it):
    WFY    within a fiscal year the opening CSM (item 1) of the quarters differs by more than max(0.5% of the max, 2억)
    CONT   a quarter's opening differs from the previous fiscal year's 4Q closing by more than max(0.5% of that closing, 2억)
    SPIKE  closing CSM moves by more than 50% against the previous quarter
    ZAMORT amortisation (item 5) is exactly 0 while an end balance is positive
* gold-overlay index (owner cells) used for the "gold conflict" exclusion
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

QS = [f"{y}.{n}Q" for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4) if f"{y}.{n}Q" <= "2026.2Q"]


def qkey(q):
    return (int(q[:4]), int(q[5]))


def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def csm_chain(rows=None):
    """{kr: {q: {1..6: value}}} from CSM_waterfall.json (억원, YTD)."""
    rows = rows if rows is not None else load_json("CSM_waterfall.json")
    ch = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        ch[r["원보험사코드"]][r["공시분기"]][r["항목번호"]] = r["값"]
    return ch


def names():
    out = {}
    for r in load_json("CSM_waterfall.json"):
        out[r["원보험사코드"]] = r["원수사명"]
    return out


def gold_csm_blocks():
    d = load_json("data/_gold/user_csm_cells.json")
    g = defaultdict(list)
    for c in d["set"]:
        g[(c["원보험사코드"], c["공시분기"])].append(c["항목번호"])
    return g, set(d.get("exclude_companies", {}))


def gold_pl_blocks():
    d = load_json("data/_gold/user_pl_cells.json")
    g = defaultdict(list)
    for c in d["set"]:
        g[(c["원보험사코드"], c["공시분기"])].append(c["항목번호"])
    return g


def confirmed_pl_cells():
    """owner-confirmed cells (data/_gold/user_pl_confirmed_cells.json): {(company name, quarter): [items]}."""
    d = load_json("data/_gold/user_pl_confirmed_cells.json")
    out = defaultdict(list)
    for c in d["cells"]:
        out[(c["company"], c["quarter"])].append((c["master"], c["item"]))
    return out


def strict_violations(chain_co, wfy_tol_rel=0.005, abs_tol=2.0):
    """chain_co = {q: {1..6}} of ONE company -> list of dict(rule, quarters(set), detail)."""
    v = []
    qs = sorted(chain_co, key=qkey)
    fys = sorted({q[:4] for q in qs})
    # WFY
    for fy in fys:
        opens = [(q, chain_co[q].get(1)) for q in qs if q[:4] == fy and chain_co[q].get(1) is not None]
        if len(opens) >= 2:
            vals = [x for _, x in opens]
            if max(vals) - min(vals) > max(wfy_tol_rel * abs(max(vals)), abs_tol):
                v.append({"rule": "WFY", "quarters": {q for q, _ in opens}, "detail": {q: round(x, 1) for q, x in opens},
                          "mag": (max(vals) - min(vals)) / max(abs(max(vals)), 1e-9)})
    # CONT: opening of FY quarters vs previous FY 4Q closing
    for q in qs:
        y = int(q[:4])
        pq = f"{y-1}.4Q"
        if pq in chain_co and chain_co[pq].get(6) is not None and chain_co[q].get(1) is not None:
            pc, o = chain_co[pq][6], chain_co[q][1]
            if abs(o - pc) > max(0.005 * abs(pc), abs_tol):
                v.append({"rule": "CONT", "quarters": {q, pq}, "detail": {"open": round(o, 1), "prev_close": round(pc, 1), "delta": round(o - pc, 1)},
                          "mag": abs(o - pc) / max(abs(pc), 1e-9)})
    # SPIKE
    for a, b in zip(qs, qs[1:]):
        if qkey(b)[0] * 4 + qkey(b)[1] - (qkey(a)[0] * 4 + qkey(a)[1]) != 1:
            continue
        p, c = chain_co[a].get(6), chain_co[b].get(6)
        if p is not None and c is not None and abs(p) > 1e-6 and abs((c - p) / p) > 0.5:
            v.append({"rule": "SPIKE", "quarters": {a, b}, "detail": {"prev": round(p, 1), "cur": round(c, 1)}, "mag": abs((c - p) / p)})
    # ZAMORT
    for q in qs:
        m = chain_co[q]
        a, o, c = m.get(5), m.get(1), m.get(6)
        if a is not None and a == 0 and ((o is not None and o > 0) or (c is not None and c > 0)):
            v.append({"rule": "ZAMORT", "quarters": {q}, "detail": {}, "mag": 1.0})
    return v


def touching(violations, q):
    return [x for x in violations if q in x["quarters"]]


def fmt_viol(vs):
    return "; ".join(f"{x['rule']}[{','.join(sorted(x['quarters'], key=qkey))}]" for x in vs)


def vsig(x):
    return (x["rule"], tuple(sorted(x["quarters"], key=qkey)))


def created_or_worse(base, new, rel=0.10, pp=0.002):
    """violations of `new` that `base` does not have, or that exist in `base` but got worse (magnitude +10% relative and +0.2pp)."""
    bm = {vsig(x): x.get("mag", 0.0) for x in base}
    out = []
    for x in new:
        k = vsig(x)
        if k not in bm:
            out.append(x)
        elif x.get("mag", 0.0) > bm[k] * (1 + rel) + pp:
            out.append({**x, "worsened_from": bm[k]})
    return out


def resolved(base, new):
    ns = {vsig(x) for x in new}
    return [x for x in base if vsig(x) not in ns]
