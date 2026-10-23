# -*- coding: utf-8 -*-
import json
p = {"generated": "2026-10-24", "tickets": {}, "scenario": "PASS2_EMPTY", "buckets": [], "csm_buckets": [], "seams": [],
     "apply_contract": {"gold_new": [], "gold_replace": [], "csm_gold_new": [], "csm_gold_replace": [], "csm_gold_remove": [], "null_dangi_add": [], "null_dangi_remove": [], "set_dangi_add": [], "set_dangi_remove": [], "held": [], "drift_fix": []}}
json.dump(p, open("p2_plan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("empty plan written")
