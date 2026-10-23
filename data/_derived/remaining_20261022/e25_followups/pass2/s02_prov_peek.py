# -*- coding: utf-8 -*-
"""pass2 s02 (read-only): print the PL provenance blocks of a company/quarter (all item blocks), compactly.
usage: s02_prov_peek.py CODE QUARTER [BLOCK substring]"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
code, q = sys.argv[1], sys.argv[2]
sub = sys.argv[3] if len(sys.argv) > 3 else ""
doc = json.load(open(f"{ROOT}/PL_breakdown_provenance.json", encoding="utf-8"))
for c in doc["cells"]:
    if c["company_code"] == code and c["quarter"] == q and sub in c["item_block"]:
        print(json.dumps(c, ensure_ascii=False, indent=1)[:3500])
        print("-----")
