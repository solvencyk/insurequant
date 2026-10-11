# -*- coding: utf-8 -*-
"""a16 (read-only): compare the LIVE site file (https://www.insurequant.com/data/dart/viz/csm_amort_schedule.json, fetched with
curl --ssl-no-revoke into the scratchpad), the origin/main copy, the pre-fix local panel and the rebuilt panel, company by company.
Usage: a16_live_compare.py <live.json> <main.json>"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
sys.stdout.reconfigure(encoding="utf-8")

live_p, main_p = Path(sys.argv[1]), Path(sys.argv[2])
live = json.loads(live_p.read_text(encoding="utf-8"))
main = json.loads(main_p.read_text(encoding="utf-8"))
pre = json.loads((ROOT / "data/_derived/amort_fix_backup_20261011/csm_amort_schedule.json.pre_fix").read_text(encoding="utf-8"))
new = json.loads((ROOT / "data/dart/viz/csm_amort_schedule.json").read_text(encoding="utf-8"))
fix = json.loads((W / "a09_panel_diff.json").read_text(encoding="utf-8"))["changed"]


def idx(p):
    return {c["company"]: c for c in p["companies"]}


L, M, P, N = idx(live), idx(main), idx(pre), idx(new)
print("sha256 live", hashlib.sha256(live_p.read_bytes()).hexdigest()[:16], "| origin/main copy", hashlib.sha256(main_p.read_bytes()).hexdigest()[:16],
      "| live == main bytes:", live_p.read_bytes() == main_p.read_bytes())
print("companies: live", len(L), "main", len(M), "pre-fix local", len(P), "rebuilt", len(N))
print("in pre-fix local but not live (reinsurers appended 2026-10-11, not yet deployed):", sorted(set(P) - set(L)))


def sched(c):
    y = c.get("yearly") or {}
    return tuple(y.get(f"y{k}") for k in range(1, 6)), (c.get("buckets") or {}).get("total")


print("\nthe 18 corrected companies: is the WRONG (pre-fix) schedule what the live site serves?")
n_live_wrong = 0
for co in fix:
    lv, pr, nw = L.get(co), P[co], N[co]
    if lv is None:
        print(f"  {co:<14s} not on the live file")
        continue
    same_pre = sched(lv) == sched(pr)
    same_new = sched(lv) == sched(nw)
    n_live_wrong += 1 if same_pre else 0
    print(f"  {co:<14s} live y1..y5 {sched(lv)[0]} total {sched(lv)[1]} | live == pre-fix: {same_pre} | live == rebuilt: {same_new} | live period {lv.get('period')} rcept {lv.get('rcept_no')}")
print(f"live file carries the pre-fix (prior-year) schedule for {n_live_wrong} of {len(fix)} corrected companies")
others = [c for c in P if c not in fix and c in L]
diff_other = [c for c in others if sched(L[c]) != sched(P[c])]
print("not-corrected companies present on live: ", len(others), "| whose live schedule differs from local (older filing on live):", diff_other)
