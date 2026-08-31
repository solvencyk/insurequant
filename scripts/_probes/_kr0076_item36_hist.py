# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = json.load(open("kics_disclosure.json", encoding="utf-8"))
rows = [r for r in data if r.get("원보험사코드")=="KR0076" and r.get("항목번호") in (36,37,39,40)]
by_q = {}
for r in rows:
    by_q.setdefault(r["공시분기"], {})[r["항목번호"]] = (r.get("값"), r.get("값_적용후"))
for q in sorted(by_q):
    print(q, by_q[q])

print()
try:
    ta = json.load(open("data/_derived/kics_transition_applicability.json", encoding="utf-8"))
    if isinstance(ta, dict):
        for k, v in ta.items():
            if "KR0076" in str(k):
                print(k, v)
    print("---checking nested structure---")
    print(type(ta))
except Exception as e:
    print("ERR", e)
