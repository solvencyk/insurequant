# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/compare/panel_compare.json", encoding="utf-8"))
print(list(d))
for k, v in d.items():
    if k != "metrics":
        print(k, str(v)[:300])
m = d["metrics"][0]
print({k: (str(v)[:100]) for k, v in m.items()})
