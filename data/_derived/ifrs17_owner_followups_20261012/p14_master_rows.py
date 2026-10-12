# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = json.loads(open("C:/Users/sangwook.cho/Desktop/insurequant/CSM_amortization.json", "rb").read().decode("utf-8"))
for i, r in enumerate(rows):
    if r["원보험사코드"] in ("KR0080", "KR0068") and r["공시분기"] == "2025.4Q":
        print(i, json.dumps(r, ensure_ascii=False))
