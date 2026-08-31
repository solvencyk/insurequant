# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open(r"C:\Users\sangwook.cho\Desktop\insurequant\data\_derived\kics_transition_applicability.json", "r", encoding="utf-8") as f:
    d = json.load(f)

# find KR0032 entries wherever they are
def walk(obj, path=""):
    if isinstance(obj, dict):
        if "KR0032" in obj:
            print(f"KEY MATCH at {path}: {json.dumps(obj['KR0032'], ensure_ascii=False)}")
        for k, v in obj.items():
            walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, dict) and item.get("원보험사코드") == "KR0032":
                print(f"LIST MATCH at {path}[{i}]: {json.dumps(item, ensure_ascii=False)}")

walk(d)
print("top-level keys:", list(d.keys())[:20] if isinstance(d, dict) else "not dict")
