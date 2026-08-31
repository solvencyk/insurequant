# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = json.load(open("kics_disclosure.json", encoding="utf-8"))
rows = [r for r in data if r.get("원보험사코드")=="KR0076" and r.get("항목번호") in range(41,47)]
by_q = {}
for r in rows:
    by_q.setdefault(r["공시분기"], {})[r["항목번호"]] = (r.get("항목명"), r.get("값"), r.get("값_적용후", "<MISSING>"))

for q in sorted(by_q):
    print(q)
    for it in range(41,47):
        if it in by_q[q]:
            name, v, vp = by_q[q][it]
            print(f"  item{it} {name!r}: 값={v!r} 값_적용후={vp!r}")
