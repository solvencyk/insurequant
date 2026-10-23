# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
plan = json.load(open("e23_plan_lotte.json", encoding="utf-8"))
C = plan["apply_contract"]
for e in C["gold_new"][:3] + C["gold_new"][-2:]:
    print(e["item"], e["quarter"], e["value"], "was", e["was"])
    print("   NOTE:", e["note"])
for e in C["csm_gold_new"][:2] + C["csm_gold_new"][-1:]:
    print("CSM", e["item"], e["quarter"], e["value"], "was", e["was"])
    print("   WHY:", e["why"])
print("null_dangi_add:", C["null_dangi_add"])
