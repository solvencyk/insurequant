# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(type(data))
if isinstance(data, dict):
    print("top keys:", list(data.keys())[:20])
    for k in list(data.keys())[:5]:
        v = data[k]
        print(k, type(v), (len(v) if hasattr(v, "__len__") else v))
elif isinstance(data, list):
    print("list len", len(data))
    print(json.dumps(data[0], ensure_ascii=False, indent=2)[:2000])
