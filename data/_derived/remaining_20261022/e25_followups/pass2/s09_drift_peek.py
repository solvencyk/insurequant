# -*- coding: utf-8 -*-
"""READ-ONLY: print the snapshot drift cells (fresh build_pl() with the live gold vs live master) for given companies, with both values."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
codes = set(sys.argv[1].split(","))
d = json.load(open("drift_before.json", encoding="utf-8"))
live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
print("total drift", len(d["drift_all"]), "csm", len(d["csm_drift_all"]))
for k in sorted(map(tuple, d["drift_all"]), key=lambda x: (x[0], x[2], x[1])):
    if k[0] in codes:
        r = live[k]
        print(k, "live 값", r["값"], "당분기", r.get("값_당분기"))
