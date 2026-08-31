# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("data/_derived/kics_transition_applicability.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("META:", json.dumps(data.get("_meta", {}), ensure_ascii=False, indent=2)[:2000])
records = data.get("records")
print("records type:", type(records), "len:", len(records) if hasattr(records,'__len__') else None)
if isinstance(records, list):
    print("sample record:", json.dumps(records[0], ensure_ascii=False, indent=2))
    for r in records:
        if isinstance(r, dict) and r.get("원보험사코드") == "KR0074":
            print("---MATCH---")
            print(json.dumps(r, ensure_ascii=False, indent=2))
elif isinstance(records, dict):
    print("records keys sample:", list(records.keys())[:20])
    if "KR0074" in records:
        print(json.dumps(records["KR0074"], ensure_ascii=False, indent=2))
