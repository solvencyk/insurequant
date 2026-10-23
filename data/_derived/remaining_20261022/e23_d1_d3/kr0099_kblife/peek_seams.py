# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = json.loads(open("e23_plan_kblife.json", encoding="utf-8").read())
for r in p["seams"]:
    if r["cls"] in ("seam", "q4_changed_but_not_adopted", "q4_unchanged_q3_adopted"):
        print(r["quarter"], r["item"], r["cls"], "D=", r["derived_after"], "live_dangi=", r["live_dangi"], "q4cmp=", r.get("q4_comp_vs_master"), "p3m=", (r.get("printed_3m") or {}).get("value"))
