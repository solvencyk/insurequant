# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = json.loads(open("e23_plan_kblife.json", encoding="utf-8").read())
for r in p["seams"]:
    print(r["quarter"], f"i{r['item']:>2}", f"{r['cls']:<32}", "D=", r["derived_after"], "live_dangi=", r["live_dangi"], "p3m=", (r.get("printed_3m") or {}).get("value"), "diff=", r.get("diff_vs_printed_3m"), "cur_ad=", r["cur_adopted"], "prev_ad=", r["prev_adopted"])
