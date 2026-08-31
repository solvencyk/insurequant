# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("data/_derived/kics_transition_applicability.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# print structure keys first
if isinstance(data, dict):
    print("top-level keys sample:", list(data.keys())[:5])
    if "KR0010" in data:
        print("KR0010 entry:", json.dumps(data["KR0010"], ensure_ascii=False, indent=2))
    else:
        # maybe nested differently
        for k in data:
            if "KR0010" in str(k) or (isinstance(data[k], dict) and "KR0010" in json.dumps(data[k], ensure_ascii=False)):
                print("found under key:", k)
elif isinstance(data, list):
    for r in data:
        if r.get("원보험사코드") == "KR0010" or r.get("company_code")=="KR0010":
            print(json.dumps(r, ensure_ascii=False))
