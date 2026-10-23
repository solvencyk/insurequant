# -*- coding: utf-8 -*-
"""Show the N7_Lotte_FY2023Q4 planner candidates (read-only) next to the LIVE master and gold."""
import json, sys, os
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
M = ROOT + "/data/_derived/remaining_20261022/e20_held_and_remaining/measure"
c = json.load(open(M + "/cands_N7_Lotte_FY2023Q4.json", encoding="utf-8"))
print("keys:", list(c.keys()))
pl = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
csm = json.load(open(ROOT + "/CSM_waterfall.json", encoding="utf-8"))
print("PL top-level type:", type(pl).__name__, (list(pl.keys())[:5] if isinstance(pl, dict) else len(pl)))
print("CSM top-level type:", type(csm).__name__, (list(csm.keys())[:5] if isinstance(csm, dict) else len(csm)))
print()
print("PL cells:", len(c["pl_cells"]))
for x in c["pl_cells"]:
    print(" ", x["code"], x["q"], x["item"], "old", x["old"], "new", x["new"], "gold", x["gold"], x.get("gold_was"))
print("CSM cells:", len(c.get("csm_cells", [])))
for x in c.get("csm_cells", []):
    print(" ", x)
for k in c:
    if k not in ("pl_cells", "csm_cells", "specs", "name"):
        print(k, "=>", str(c[k])[:600])
