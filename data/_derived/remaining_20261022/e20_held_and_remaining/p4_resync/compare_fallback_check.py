# -*- coding: utf-8 -*-
import json
d = json.load(open("data/compare/panel_compare.json", encoding="utf-8"))
qs = d["meta"]["quarters"]
for mid in ("ins_profit", "net_income", "roe", "inv_profit"):
    m = next(x for x in d["metrics"] if x["id"] == mid)
    for code in ("KR0032", "KR0082", "KR0083"):
        a = m["v"].get(code, [])
        print(mid, code, "latest idx value:", a[-1] if a else None, "(", qs[len(a)-1] if a else "-", ") non-null last:", next((qs[i] for i in range(len(a)-1, -1, -1) if a[i] is not None), None))
