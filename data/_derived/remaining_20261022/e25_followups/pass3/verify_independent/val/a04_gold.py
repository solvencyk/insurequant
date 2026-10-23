# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
g = json.load(open(R + "data/_gold/user_pl_cells.json", encoding="utf-8"))
print(type(g), list(g)[:10] if isinstance(g, dict) else len(g))
for k, v in g.items():
    if isinstance(v, (list, dict)):
        print(k, type(v).__name__, len(v))
    else:
        print(k, str(v)[:300])
