# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
prov = json.load(open(f"{ROOT}/PL_breakdown_provenance.json", encoding="utf-8"))
print([k for k in prov if k != "cells"])
code, q = sys.argv[1], sys.argv[2]
for c in prov["cells"]:
    if c["company_code"] == code and c["quarter"] == q:
        print("BLOCK", c["item_block"], "keys", list(c.keys()))
        s = json.dumps(c, ensure_ascii=False)
        print(s[:int(sys.argv[3]) if len(sys.argv) > 3 else 1800])
