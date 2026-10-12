# -*- coding: utf-8 -*-
"""Read-only: census of None (blank) 상각액 cells per (company, quarter) in CSM_amortization.json."""
import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
rows = json.loads(open("C:/Users/sangwook.cho/Desktop/insurequant/CSM_amortization.json", "rb").read().decode("utf-8"))
d = collections.defaultdict(dict)
for r in rows:
    d[(r["원보험사코드"], r["원수사명"], r["공시분기"])][r["경과차년"]] = r["상각액"]
for k, v in sorted(d.items()):
    blanks = [i for i in range(1, 11) if v.get(i) is None]
    if blanks:
        print(k, "blank years:", blanks)
print("total buckets", len(d))
