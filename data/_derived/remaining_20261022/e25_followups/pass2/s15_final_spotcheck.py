# -*- coding: utf-8 -*-
"""READ-ONLY final spot check of the live PL master after the apply."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
by = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
for k in [("KR0070", 5, "2024.1Q"), ("KR0070", 7, "2024.1Q"), ("KR0070", 9, "2024.2Q"), ("KR0070", 5, "2025.3Q"), ("KR0070", 7, "2025.3Q"), ("KR0070", 12, "2023.1Q"),
          ("KR0087", 5, "2024.3Q"), ("KR0087", 6, "2024.3Q"), ("KR0087", 7, "2024.3Q"), ("KR0009", 5, "2023.2Q"), ("KR0068", 5, "2023.2Q"), ("KR0068", 6, "2023.2Q"), ("KR0068", 7, "2023.2Q"),
          ("KR0032", 31, "2023.1Q"), ("KR0082", 25, "2023.2Q"), ("KR0005", 16, "2024.3Q")]:
    r = by[k]
    print(k, "값", r["값"], "당분기", r.get("값_당분기"))
print("rows", len(by))
