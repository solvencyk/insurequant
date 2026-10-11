#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""All PL_breakdown master cells of one company at given quarters (read-only).  usage: bspl_followup_pl_cells.py KR0003 2023.1Q 2023.2Q"""
import json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
code, qs = sys.argv[1], sys.argv[2:]
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
rows = defaultdict(dict)
nm = {}
for r in pl:
    if r["원보험사코드"] == code and r["공시분기"] in qs:
        rows[str(r["항목번호"])][r["공시분기"]] = r["값"]
        nm[str(r["항목번호"])] = r["항목명"]
def key(k):
    a = k.split("-")
    return tuple(int(x) if x.isdigit() else 0 for x in a)
print(f"{'item':>5} {'name':<26}" + "".join(f"{q:>16}" for q in qs))
for it in sorted(rows, key=key):
    print(f"{it:>5} {nm[it][:24]:<26}" + "".join((f"{rows[it][q]:>16,.1f}" if rows[it].get(q) is not None else f"{'-':>16}") for q in qs))
