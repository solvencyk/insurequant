# -*- coding: utf-8 -*-
"""READ-ONLY: provenance blocks that differ between the live sidecar and the simulated post-apply sidecar (pass4/sim_out)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
EV = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass4"
a = json.load(open(f"{ROOT}/PL_breakdown_provenance.json", encoding="utf-8"))
b = json.load(open(f"{EV}/sim_out/PL_breakdown_provenance.json", encoding="utf-8"))
ka = {(c["company_code"], c["quarter"], c["item_block"]): c for c in a["cells"]}
kb = {(c["company_code"], c["quarter"], c["item_block"]): c for c in b["cells"]}
print("blocks live", len(ka), "sim", len(kb))
for k in sorted(set(ka) | set(kb)):
    if ka.get(k) != kb.get(k):
        print("=====", k)
        print("  LIVE:", json.dumps(ka.get(k), ensure_ascii=False)[:1400])
        print("  NEW :", json.dumps(kb.get(k), ensure_ascii=False)[:1400])
print("top-level key diff:", sorted(set(b) - set(a)), sorted(set(a) - set(b)))
