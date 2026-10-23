# -*- coding: utf-8 -*-
"""READ-ONLY: print the single-quarter seam table of p2_plan.json (derived single quarter vs the printed 3-month column)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = json.load(open("p2_plan.json", encoding="utf-8"))
for s in p["seams"]:
    print(f"{s['code']} {s['quarter']} item {s['item']:>2}: derived {s['derived_after']:>14} printed 3M {s['printed_3m']['value']:>14} diff {s['diff_vs_printed_3m']:>8} {s['cls']} {s['proposal']}")
