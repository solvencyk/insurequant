# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("data/_derived/kics_transition_applicability.json", "r", encoding="utf-8") as f:
    data = json.load(f)

records = data["records"]
matches = [r for r in records if r.get("code") == "KR0074"]
print(f"Total KR0074 records: {len(matches)}")
for r in matches:
    print(json.dumps(r, ensure_ascii=False, indent=2))
