# -*- coding: utf-8 -*-
"""read-only: print CSM + PL cells of the planner output e23_plan_hd.json compactly"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
P = json.loads((Path(__file__).resolve().parent / "e23_plan_hd.json").read_text(encoding="utf-8"))
for cb in P["csm_buckets"]:
    print("CSM", cb["quarter"], cb["file"] if "file" in cb else "", "two_dp", cb["two_dp"], "vec", cb["vec"], "old", cb["old"], "closure", cb["closure_resid"])
    for c in cb["cells"]:
        print("   item", c["item"], c["item_name"], "old", c["old"], "new", c["new"], "exact", c["exact"], "cand", c["cand_new"], "derived", c.get("derived"))
        for p in c["parts"]:
            print("        part", json.dumps(p, ensure_ascii=False)[:300])
for b in P["buckets"]:
    print("PL", b["quarter"], "cells", len(b["cells"]), [c["item"] for c in b["cells"]], "closure_ok", b["closure_ok"])
    for c in b["cells"]:
        if c["item"] in (4, 13, 14, 2, 16, 1):
            print("   item", c["item"], "old", c["old"], "new", c["new"], "cand", c["cand_new"], "kind", c["kind"], "parts", json.dumps(c["parts"], ensure_ascii=False)[:420])
