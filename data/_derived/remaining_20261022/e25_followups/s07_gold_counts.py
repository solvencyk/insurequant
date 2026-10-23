# -*- coding: utf-8 -*-
"""READ-ONLY: gold set sizes, dangi pin counts and ledger size (declared GOLD_OVERLAY_CENSUS check)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant"
p = json.load(open(f"{R}/data/_gold/user_pl_cells.json", encoding="utf-8"))
c = json.load(open(f"{R}/data/_gold/user_csm_cells.json", encoding="utf-8"))
l = json.load(open(f"{R}/data/_gold/gold_overlay_ledger.json", encoding="utf-8"))
print("PL set", len(p["set"]), "null_dangi", len(p["null_dangi"]["cells"]), "set_dangi", len(p["set_dangi"]["cells"]), "keys", list(p.keys()))
print("CSM set", len(c["set"]), "keys", list(c.keys()))
print("ledger entries", len(l["entries"]), "PL pins", sum(1 for k in l["entries"] if k.startswith("PL|")), "CSM pins", sum(1 for k in l["entries"] if k.startswith("CSM|")))
print("PL null_dangi doc:", {k: (v if k != "cells" else "...") for k, v in p["null_dangi"].items()})
print("PL set_dangi doc:", {k: (v if k != "cells" else "...") for k, v in p["set_dangi"].items()})
print("PL _doc:", str(p["_doc"])[:600])
print("CSM _doc:", str(c.get("_doc"))[:600])
