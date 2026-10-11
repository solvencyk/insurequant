import json
from pathlib import Path
D = Path(__file__).resolve().parent
b = json.loads((D/"xlsx_before.json").read_text(encoding="utf-8"))["요약"]["rows"]
a = json.loads((D/"xlsx_after.json").read_text(encoding="utf-8"))["요약"]["rows"]
assert len(a) == len(b)
for x, y in zip(b, a):
    if x != y:
        xv, yv = json.loads(x), json.loads(y)
        print([ (p, q) for p, q in zip(xv, yv) if p != q], "| sheet:", xv[0])
