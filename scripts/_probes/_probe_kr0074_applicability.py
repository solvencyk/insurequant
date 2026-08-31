# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("data/_derived/kics_transition_applicability.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# find structure
if isinstance(data, dict):
    print("TOP KEYS:", list(data.keys())[:20])
    # try to find KR0074
    def search(obj, path=""):
        if isinstance(obj, dict):
            if "KR0074" in obj:
                print(f"FOUND at {path}: KR0074 ->")
                print(json.dumps(obj["KR0074"], ensure_ascii=False, indent=2))
            for k, v in obj.items():
                search(v, path + "/" + str(k))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, dict) and item.get("원보험사코드") == "KR0074":
                    print(f"FOUND in list at {path}[{i}]:")
                    print(json.dumps(item, ensure_ascii=False, indent=2))
    search(data)
elif isinstance(data, list):
    print("LIST length:", len(data))
    for item in data:
        if isinstance(item, dict) and ("KR0074" in json.dumps(item, ensure_ascii=False)):
            print(json.dumps(item, ensure_ascii=False, indent=2))
