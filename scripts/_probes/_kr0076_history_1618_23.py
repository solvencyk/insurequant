# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = json.load(open("kics_disclosure.json", encoding="utf-8"))
rows = [r for r in data if r.get("원보험사코드")=="KR0076" and r.get("항목번호") in (14,15,16,17,18,19,20,21,22,23)]
by_q = {}
for r in rows:
    by_q.setdefault(r["공시분기"], {})[r["항목번호"]] = (r.get("값"), r.get("값_적용후"))

for q in sorted(by_q):
    row = by_q[q]
    print(q, {k: row.get(k) for k in (14,15,16,17,18,19,20,21,22,23)})
