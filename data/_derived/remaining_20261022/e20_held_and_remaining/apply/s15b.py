# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
lp = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown_provenance.json", encoding="utf-8"))
for c in lp["cells"]:
    if c["company_code"] == "KR0082" and c["quarter"] == "2023.1Q" and c["item_block"] == "income_statement":
        s = json.dumps(c, ensure_ascii=False)
        print(len(s)); print(s[:1800])
for c in lp["cells"]:
    if c["company_code"] == "KR0087" and c["quarter"] == "2025.1Q" and c["item_block"] == "income_statement":
        s = json.dumps(c, ensure_ascii=False)
        print(len(s)); print(s[:1800])
