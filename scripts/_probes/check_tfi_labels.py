# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
data = json.load(open("kics_disclosure.json", encoding="utf-8"))

# KR0079 2023.3Q items 47-49 labels
for r in data:
    if r["원보험사코드"] == "KR0079" and r["공시분기"] == "2023.3Q" and r["항목번호"] in (47,48,49):
        print("KR0079 2023.3Q", r["항목번호"], repr(r["항목명"]))

print("---")
# find a company with all of 47-54 present, print labels once
seen_items = set()
for r in data:
    if r["항목번호"] in range(47,55) and r["항목번호"] not in seen_items:
        print(r["원보험사코드"], r["공시분기"], r["항목번호"], repr(r["항목명"]))
        seen_items.add(r["항목번호"])
    if len(seen_items) == 8:
        break
