# -*- coding: utf-8 -*-
import json, sys
a = json.load(open(sys.argv[1], encoding="utf-8"))
b = json.load(open(sys.argv[2], encoding="utf-8"))
qs = b["meta"]["quarters"]
names = {c["code"]: c["name"] for c in b["companies"]}
n = 0
for ma, mb in zip(a["metrics"], b["metrics"]):
    for code in sorted(set(ma["v"]) | set(mb["v"])):
        va, vb = ma["v"].get(code), mb["v"].get(code)
        if va != vb:
            for i, (x, y) in enumerate(zip(va or [], vb or [])):
                if x != y:
                    n += 1
                    print(f"{mb['id']:12s} {code} {names.get(code)} {qs[i]}: {x} -> {y}")
    for k in mb:
        if k != "v" and ma.get(k) != mb.get(k):
            print("non-v field differs:", mb["id"], k)
print("changed values:", n)
for k in ("meta", "companies", "loss_curve"):
    print(k, "identical" if a[k] == b[k] else "DIFFERENT")
