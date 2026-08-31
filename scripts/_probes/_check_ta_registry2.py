# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ta = json.load(open("data/_derived/kics_transition_applicability.json", encoding="utf-8"))
print("meta:", json.dumps(ta.get("_meta"), ensure_ascii=False)[:300])
recs = ta.get("records")
print(type(recs), len(recs) if hasattr(recs,'__len__') else '?')
if isinstance(recs, list):
    for r in recs:
        if r.get("원보험사코드")=="KR0076" or r.get("company")=="KR0076" or r.get("code")=="KR0076":
            print(json.dumps(r, ensure_ascii=False))
elif isinstance(recs, dict):
    for k,v in recs.items():
        if "KR0076" in str(k):
            print(k, json.dumps(v, ensure_ascii=False))
