#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""List the remaining HOLD_UNTESTED / HOLD_TRIO / HOLD_PARTIAL_GROUP / HOLD_QOQ candidates (read-only)."""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / "data/_derived/bspl_granularity_20261011/candidates"
want = set(sys.argv[1:]) or {"HOLD_UNTESTED", "HOLD_TRIO", "HOLD_PARTIAL_GROUP", "HOLD_QOQ"}
tot = Counter()
g = defaultdict(list)
for p in sorted(CAND.glob("KR*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    for c in d["candidates"]:
        tot[c["status"]] += 1
        if c["status"] in want:
            g[(d["code"], c["item"], c["status"], c["rule"], c["kind"], c.get("form"), "zero" if abs(c.get("value_mn") or 0) < 1e-9 else "nz")].append(c)
print(dict(tot))
for k, lst in sorted(g.items()):
    qs = ",".join(c["quarter"][2:] for c in sorted(lst, key=lambda c: c["quarter"]))
    vals = ",".join(f"{c['value_mn']/100:,.0f}" for c in sorted(lst, key=lambda c: c["quarter"]))
    print(f"{k[0]}|{k[1]:>2} {k[2]:<19} {k[6]:<4} {k[3]}|{k[4]}|{k[5]} n={len(lst)} {qs}  vals(억)={vals[:90]}  {(lst[0].get('note') or '')[:80]}")
