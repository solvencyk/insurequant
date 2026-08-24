# -*- coding: utf-8 -*-
"""Read-only: 36_irr derivation vs disclosed, all quarters, for given companies."""
import json, sys, io, math
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
CODES = sys.argv[1].split(",")

def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

by = {}
for r in recs:
    if r.get("원보험사코드") not in CODES:
        continue
    by.setdefault((r["원보험사코드"], r["공시분기"]), {})[int(r["항목번호"])] = f(r.get("값"))

print(f"{'q':>9} | {'i36공시':>10} | {'derived':>10} | {'diff':>9} | {'rel%':>7} | {'tol5%':>8} | {'>tol?':>5}")
for k in sorted(by):
    d = by[k]
    if any(d.get(i) is None for i in (36, 41, 42, 43, 44, 45, 46)):
        continue
    b = d[41]
    mr, up, dn, fl, tw = (b - d[42], b - d[43], b - d[44], b - d[45], b - d[46])
    exp = math.sqrt(max(up, dn) ** 2 + max(fl, tw) ** 2) + mr
    diff = d[36] - exp
    tol = max(2.0, 0.05 * abs(exp))
    print(f"{k[0]} {k[1]:>7} | {d[36]:10.2f} | {exp:10.2f} | {diff:9.2f} | "
          f"{100*diff/exp:7.2f} | {tol:8.2f} | {'RED' if abs(diff)>tol else 'ok':>5}")
