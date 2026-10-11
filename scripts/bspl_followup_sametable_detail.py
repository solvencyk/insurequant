#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detail of held candidates of one company/item: per cell rule/kind/form/page/value and the calibration evidence entries of that filing.
  usage: bspl_followup_sametable_detail.py KR0004 13 [24 ...]
"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / "data/_derived/bspl_granularity_20261011/candidates"
code = sys.argv[1]
items = [int(x) for x in sys.argv[2:]]
d = json.loads((CAND / f"{code}.json").read_text(encoding="utf-8"))
mv = {}
import json as _j
bs = _j.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
for r in bs:
    if r.get("회사코드") == code or r.get("code") == code:
        pass
for item in items:
    print(f"\n=== {code} item {item} {d.get('name')}")
    for c in sorted((c for c in d["candidates"] if c["item"] == item), key=lambda c: c["quarter"]):
        print(f"  {c['quarter']} {c['status']:<20} {c['rule']:<28} {c['kind']:<7} {c.get('form')} p{c.get('page')} val={c.get('value_mn')} unit={c.get('unit')} master={c.get('master')}")
        ck = f"{c['rule']}|{c.get('form')}"
        ev = d["calibration"].get(ck, {}).get("evidence", [])
        mine = [e for e in ev if e[0] == c["quarter"]]
        for e in mine:
            print("       ev:", e)
