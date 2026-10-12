# -*- coding: utf-8 -*-
import json
from pathlib import Path
D = Path(__file__).resolve().parent
b = json.loads((D / "xlsx_before.json").read_text(encoding="utf-8"))["보험계약부채"]["rows"]
a = json.loads((D / "xlsx_after.json").read_text(encoding="utf-8"))["보험계약부채"]["rows"]
print(len(b), len(a))
n = 0
for i, (x, y) in enumerate(zip(b, a)):
    if x != y:
        xv, yv = json.loads(x), json.loads(y)
        print(i, [(j, p, q) for j, (p, q) in enumerate(zip(xv, yv)) if p != q][:4])
        n += 1
        if n >= 4:
            break
print(json.loads(a[0]))
