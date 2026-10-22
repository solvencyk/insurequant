#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 13: peek the apply contract of e20_plan.json (notes of a few cells, pin lists) -> stdout"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / "e20_plan.json").read_text(encoding="utf-8"))
c = plan["apply_contract"]
for key in ("gold_new", "gold_replace"):
    arr = c[key]
    print(f"##### {key}: {len(arr)}")
    pick = [arr[0], arr[len(arr) // 2], arr[-1]] if key == "gold_new" else [arr[0], arr[-1]]
    for e in pick:
        print(f"  {e['code']} {e['quarter']} i{e['item']} value={e['value']} was={e['was']}")
        print("    note:", e["note"])
print("##### null_dangi_add", len(c["null_dangi_add"]))
from collections import Counter
print(Counter((x[0], x[1]) for x in c["null_dangi_add"]))
print("##### set_dangi_add")
for x in c["set_dangi_add"]:
    print("  ", x)
print("##### set_dangi_remove", c["set_dangi_remove"])
print("##### held", c["held"])
