# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("data/_derived/kics_transition_applicability.json", "r", encoding="utf-8") as f:
    data = json.load(f)

recs = data["records"]
print("total records:", len(recs))
print("sample record:", json.dumps(recs[0], ensure_ascii=False, indent=2))
matches = [r for r in recs if r.get("원보험사코드")=="KR0010" or r.get("company_code")=="KR0010" or "KR0010" in json.dumps(r, ensure_ascii=False)]
print(f"\nKR0010 matches: {len(matches)}")
for m in matches:
    print(json.dumps(m, ensure_ascii=False))
