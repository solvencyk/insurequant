# -*- coding: utf-8 -*-
"""READ-ONLY: the last drift snapshot (cells where a fresh build_pl() with the live gold differs from the live master) of the previous load; prints per-company counts and the KR0010/KR0070/KR0099/KR0104 cells."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb_load2/drift_before.json"
import os
if not os.path.exists(p):
    p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0070_abl/drift_before.json"
d = json.load(open(p, encoding="utf-8"))
print(p, d.get("made_at"), "keys", list(d.keys()))
print("by_company", d["by_company"])
for k in d["drift_all"]:
    if k[0] in ("KR0010", "KR0070", "KR0099", "KR0104"):
        print("PL drift", k)
print("CSM drift n", len(d["csm_drift_all"]), d["csm_drift_all"][:10])
