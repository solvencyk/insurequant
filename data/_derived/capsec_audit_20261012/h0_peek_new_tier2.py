# -*- coding: utf-8 -*-
import json
d = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/kics_tier2_utilization.json", encoding="utf-8"))
print({k: d[k] for k in d if k != "results"} if isinstance(d, dict) else type(d))
rows = d["results"]
print(len(rows))
r = [x for x in rows if x["code"] == "KR0001"][0]
print(json.dumps(r, ensure_ascii=False, indent=1))
