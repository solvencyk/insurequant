# -*- coding: utf-8 -*-
import json, sys
from collections import Counter
a = json.load(open(sys.argv[1], encoding="utf-8"))
b = json.load(open(sys.argv[2], encoding="utf-8"))
diffs = []
def walk(x, y, path):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y), key=str):
            if k not in x: diffs.append((path + [k], "<absent>", "added"))
            elif k not in y: diffs.append((path + [k], "removed", "<absent>"))
            else: walk(x[k], y[k], path + [k])
    elif isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y): diffs.append((path, f"len{len(x)}", f"len{len(y)}")); 
        for i, (p, q) in enumerate(zip(x, y)): walk(p, q, path + [i])
    elif x != y:
        diffs.append((path, x, y))
walk(a, b, [])
print("leaf diffs:", len(diffs))
top = Counter(str(d[0][:2]) for d in diffs)
for k, n in sorted(top.items()): print(" ", k, n)
for p, x, y in diffs[:int(sys.argv[3]) if len(sys.argv) > 3 else 60]:
    print("   ", "/".join(map(str, p)), x, "->", y)
