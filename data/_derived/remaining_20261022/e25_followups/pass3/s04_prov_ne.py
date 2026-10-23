# -*- coding: utf-8 -*-
"""pass3 s04 (read-only): which provenance blocks does the planned apply replace, and for which of them does the live sidecar differ from the emitter output on the LIVE masters (hand-written content that would be lost)?"""
import importlib.util
import json
import sys
sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("p3_apply", "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/p3_apply.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
P = m.plan_all()
print("targets:", P["prov_targets"])
print("live sidecar != emitter(live) on:", P["prov_live_ne"])
live_prov = P["live"]["PROV"].obj
new_prov = P["new_prov"]
lk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in live_prov["cells"]}
nk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in new_prov["cells"]}
for k in P["prov_live_ne"]:
    a, b = lk[k], nk[k]
    print("BLOCK", k)
    for f in sorted(set(a) | set(b)):
        if a.get(f) != b.get(f):
            print("  field", f)
            print("    live:", json.dumps(a.get(f), ensure_ascii=False)[:1500])
            print("    new :", json.dumps(b.get(f), ensure_ascii=False)[:1500])
