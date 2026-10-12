# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
raw = open(R + "insurance_liability_portfolio.json", "rb").read()
rows = json.loads(raw.decode("utf-8"))
for i, r in enumerate(rows):
    if r["원보험사코드"] == "KR0100" and r["공시분기"] == "2024.1Q":
        print(i, json.dumps(r, ensure_ascii=False))
# order of keys, dup check
seen = {}
for i, r in enumerate(rows):
    k = (r["원보험사코드"], r["공시분기"], r["항목번호"])
    if k in seen:
        print("DUP", k, seen[k], i)
    seen[k] = i
print("rows", len(rows), "keys", len(seen))
print("dump roundtrip:", json.dumps(rows, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8") == raw)
