# -*- coding: utf-8 -*-
"""READ-ONLY: provenance sidecar blocks (PL_breakdown_provenance.json) for a company (and optional quarters); prints each block's keys and a compact view.
usage: s02_prov_peek.py CODE [QUARTERS(comma)] [BLOCK-substr]"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
code = sys.argv[1]
qs = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else None
blk = sys.argv[3] if len(sys.argv) > 3 else None
d = json.load(open(f"{ROOT}/PL_breakdown_provenance.json", encoding="utf-8"))
print("top-level keys:", [k for k in d.keys() if k != "cells"])
n = 0
for c in d["cells"]:
    if c["company_code"] != code:
        continue
    if qs and c["quarter"] not in qs:
        continue
    if blk and blk not in c["item_block"]:
        continue
    n += 1
    print(json.dumps(c, ensure_ascii=False)[:1800])
print("blocks:", n)
