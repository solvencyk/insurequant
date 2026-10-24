# -*- coding: utf-8 -*-
"""READ-ONLY: provenance blocks of KR0087 (2024.1Q/2024.2Q/2024.3Q/2025.2Q/2025.3Q) and KR0032 (2023.1Q/2023.2Q) in PL_breakdown_provenance.json"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
prov = json.load(open(f"{ROOT}/PL_breakdown_provenance.json", encoding="utf-8"))
print("top keys:", [k for k in prov.keys() if k != "cells"])
print("n cells:", len(prov["cells"]))
want = {("KR0087", "2024.1Q"), ("KR0087", "2024.2Q"), ("KR0087", "2024.3Q"), ("KR0087", "2025.2Q"), ("KR0087", "2025.3Q"), ("KR0032", "2023.1Q"), ("KR0032", "2023.2Q"), ("KR0032", "2023.3Q")}
for c in prov["cells"]:
    if (c["company_code"], c["quarter"]) in want:
        s = json.dumps(c, ensure_ascii=False)
        print("=====", c["company_code"], c["quarter"], c["item_block"], "len", len(s))
        print(s[:1500])
