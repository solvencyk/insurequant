# -*- coding: utf-8 -*-
"""read-only: print the apply_contract of the planner output e23_plan_abl.json (counts, held, sample notes, csm why, seams)"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / "e23_plan_abl.json").read_text(encoding="utf-8"))
C = plan["apply_contract"]
print("keys", list(C.keys()))
for k, v in C.items():
    print(k, len(v) if hasattr(v, "__len__") else v)
print("held", C["held"])
print("--- gold_new sample (first 2)")
for e in C["gold_new"][:2]:
    print(json.dumps(e, ensure_ascii=False, indent=1))
print("--- gold_replace")
for e in C["gold_replace"]:
    print(json.dumps({k: v for k, v in e.items() if k != "old_entry"}, ensure_ascii=False, indent=1))
print("--- csm_gold_new sample (first 2)")
for e in C["csm_gold_new"][:2]:
    print(json.dumps(e, ensure_ascii=False, indent=1))
print("--- csm_gold_replace")
for e in C["csm_gold_replace"]:
    print(json.dumps({k: v for k, v in e.items() if k != "old_entry"}, ensure_ascii=False, indent=1))
print("--- seams", len(plan["seams"]))
for s in plan["seams"][:80]:
    print(" ", {k: v for k, v in s.items() if k in ("code", "quarter", "item", "class", "action", "reason", "printed_3m", "D", "live", "cum_diff")})
print("--- findings")
for f in plan["findings"]:
    print(" ", f)
print("--- notes")
for n in plan["notes"]:
    print(" ", n)
print("--- csm_gold_class", plan["csm_gold_class"])
