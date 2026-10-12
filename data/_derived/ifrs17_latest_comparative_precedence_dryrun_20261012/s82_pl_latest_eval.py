"""Read-only: build the LATEST-comparative PL block for company-quarters (Tier-1 FS-API comparative + production Tier-2 chain on the comparative columns) and test it with the gate arithmetic.

usage: python s82_pl_latest_eval.py [--sumcheck] KR0008:2024.1Q KR0008:2024.2Q ...      (prior quarter = later minus one year)
output: cand/pl_latest_blocks.json (merged by key '<KR>|<prior quarter>'), plus a printed table.
Closure (백만원): B1 1 = 2+13+14(+15-16) ; I1 20 = 1+17 ; I2 22 = 20+21 ; I3 24 = 22-23 ; B3 3 = 4+5+6+7 ; AMORT |item4|/100 vs |CSM wf item5| (억) <= max(0.1억, 0.05%).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import plprior as P  # noqa: E402  (chdir -> repo root)

HERE = P.HERE
ROOT = P.ROOT
args = [a for a in sys.argv[1:] if not a.startswith("--")]
sumcheck = "--sumcheck" in sys.argv
M, NAMES, WF5 = {}, {}, {}
for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8")):
    M[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r["값"]
for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")):
    NAMES[r["원보험사코드"]] = r["원수사명"]
    if r["항목번호"] == 5:
        WF5[(r["원보험사코드"], r["공시분기"])] = r["값"]
ALL = json.loads((HERE / "cand" / "CSM_waterfall.ALLTRUSTED.json").read_text(encoding="utf-8"))
WF5_LAT = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in ALL if r["항목번호"] == 5}


def closed(res, exp, tol_abs=200.0, tol_rel=0.001):
    return abs(res) <= max(tol_rel * abs(exp), tol_abs)


def bridge(v):
    out = {}
    legs = [v.get(2), v.get(13), v.get(14)]
    if v.get(1) is not None and None not in legs:
        bare = sum(legs)
        adj = bare + (v.get(15) or 0) - (v.get(16) or 0)
        rb, ra = v[1] - bare, v[1] - adj
        out["B1"] = (bool(closed(rb, bare) or closed(ra, adj)), round(min(rb, ra, key=abs), 1))
    for name, l, rs in (("I1", 20, (1, 17)), ("I2", 22, (20, 21))):
        if v.get(l) is not None and all(v.get(i) is not None for i in rs):
            res = v[l] - sum(v[i] for i in rs)
            out[name] = (bool(closed(res, v[l])), round(res, 1))
    if None not in (v.get(24), v.get(22), v.get(23)):
        res = v[24] - (v[22] - v[23])
        out["I3"] = (bool(closed(res, v[24])), round(res, 1))
    if v.get(3) is not None and None not in (v.get(4), v.get(5), v.get(6), v.get(7)):
        res = v[3] - (v[4] + v[5] + v[6] + v[7])
        out["B3"] = (bool(closed(res, v[3])), round(res, 1))
    return out


def amort(v, wf):
    if v.get(4) is None or wf is None:
        return None
    r = abs(v[4]) / 100.0 - abs(wf)
    return (bool(abs(r) <= max(0.1, 0.0005 * abs(wf))), round(r, 2))


store_path = HERE / "cand" / "pl_latest_blocks.json"
store = json.loads(store_path.read_text(encoding="utf-8")) if store_path.exists() else {}
for spec in args:
    kr, later = spec.split(":")
    prior_q = f"{int(later[:4]) - 1}{later[4:]}"
    trace = []
    v, div, t2 = P.latest_block(kr, NAMES.get(kr), later, sumcheck=sumcheck, trace=trace)
    cur = {i: M.get((kr, prior_q, i)) for i in range(1, 33)}
    b_cur, b_lat = bridge(cur), bridge(v)
    a_cur = amort(cur, WF5.get((kr, prior_q)))
    a_lat = amort(v, WF5_LAT.get((kr, prior_q)))
    a_mix = amort(v, WF5.get((kr, prior_q)))
    n_diff = sum(1 for i in range(1, 33) if v.get(i) is not None and cur.get(i) != v.get(i))
    print("=" * 110)
    print(f"{kr} {NAMES.get(kr)} {prior_q} <- {later} comparative | Tier-1 basis {div} | sumcheck={sumcheck} {[t[0] for t in trace]}")
    print("   bridge current:", b_cur)
    print("   bridge latest :", b_lat)
    print("   amort(cur PL vs cur wf):", a_cur, "| amort(lat PL vs lat wf):", a_lat, "| amort(lat PL vs cur wf):", a_mix, "| items differing:", n_diff)
    store[f"{kr}|{prior_q}|{'sumcheck' if sumcheck else 'prod'}"] = {
        "later": later, "tier1_basis": div, "block": {str(i): v.get(i) for i in range(1, 33) if v.get(i) is not None},
        "bridge_current": b_cur, "bridge_latest": b_lat, "amort_cur": a_cur, "amort_lat_vs_lat_wf": a_lat, "amort_lat_vs_cur_wf": a_mix,
        "n_items_differing": n_diff, "trace": [[t[0], t[1], t[2]] for t in trace]}
store_path.write_text(json.dumps(store, ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")
