# -*- coding: utf-8 -*-
import json
d = json.load(open("data/compare/panel_compare.json", encoding="utf-8"))
print([k for k in d])
for i in (4, 5, 6, 16):
    m = d["metrics"][i]
    print(i, {k: (v if k != "v" else "...") for k, v in m.items()})
