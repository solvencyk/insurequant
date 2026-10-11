#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""List the Stage-B candidate records of one company (optionally one item): quarter, status, value, rule, kind, page (read-only).
usage: bspl_apply_cand_status.py KR1098 [item ...]"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
code = sys.argv[1]
items = {int(x) for x in sys.argv[2:]}
d = json.loads((ROOT / f"data/_derived/bspl_granularity_20261011/candidates/{code}.json").read_text(encoding="utf-8"))
keys = [k for k in d.keys() if k != "candidates"]
print("top keys:", keys)
for c in sorted(d["candidates"], key=lambda c: (c["item"], c["quarter"])):
    if items and c["item"] not in items:
        continue
    print(c["item"], c["quarter"], c["status"], c.get("value_mn"), c.get("master"), c.get("rule"), c.get("kind"), c.get("page"), (c.get("note") or "")[:80])
