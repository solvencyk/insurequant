#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compact view of sametable_report.json grouped by (company,item,verdict)."""
import json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
rep = json.loads((ROOT / "data/_derived/bspl_followup_20261011/sametable_report.json").read_text(encoding="utf-8"))
g = defaultdict(list)
for r in rep:
    code, item, q = r["key"].split("|")
    g[(code, int(item), r["verdict"])].append((q, r))
want = sys.argv[1] if len(sys.argv) > 1 else None
for (code, item, v), lst in sorted(g.items()):
    if want and v != want:
        continue
    qs = ",".join(q[2:] for q, _ in lst)
    print(f"{code}|{item:>2} {v:<18} n={len(lst):>2} {qs}")
    print("      ", lst[0][1].get("rule"), "|", (lst[0][1].get("reason") or "")[:200])
