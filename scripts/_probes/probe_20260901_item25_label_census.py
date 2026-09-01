# -*- coding: utf-8 -*-
import json, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
rows = json.loads(open("kics_disclosure.json", encoding="utf-8").read())
c = Counter()
for r in rows:
    if str(r.get("항목번호")) == "25":
        c[r.get("항목명")] += 1
for label, n in c.most_common():
    print(f"{n:5d}  {label!r}")
