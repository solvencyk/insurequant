# -*- coding: utf-8 -*-
"""Read-only: print the csm_amort_schedule.json panel entries for given company-name substrings."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/dart/viz/csm_amort_schedule.json"
d = json.loads(open(p, "rb").read().decode("utf-8"))
print("top keys:", [k for k in d.keys()])
for c in d["companies"]:
    nm = c.get("company", "")
    if any(s in nm for s in sys.argv[1:]):
        print("=" * 80)
        for k, v in c.items():
            print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:400]}")
