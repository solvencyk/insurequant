# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
data = json.load(open("kics_disclosure.json", encoding="utf-8"))
# find any row with item in 47-54, print a handful of distinct (code,q) examples with full item47-54 set
from collections import defaultdict
buckets = defaultdict(dict)
for r in data:
    if r["항목번호"] in (47,48,49,50,51,52,53,54):
        buckets[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = (r.get("값"), r.get("값_적용후", "<absent>"))

count = 0
for k, v in buckets.items():
    if 53 in v or 54 in v:
        print(k, v)
        count += 1
    if count >= 6:
        break
