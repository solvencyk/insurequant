# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open(r"C:\Users\sangwook.cho\Desktop\insurequant\data\_derived\kics_transition_applicability.json", "r", encoding="utf-8") as f:
    d = json.load(f)

recs = d["records"]
print("records type:", type(recs), "len:", len(recs) if hasattr(recs, "__len__") else "?")
if isinstance(recs, list):
    print("sample:", json.dumps(recs[0], ensure_ascii=False))
    hits = [r for r in recs if "KR0032" in json.dumps(r, ensure_ascii=False)]
    print("KR0032 hits:", len(hits))
    for h in hits:
        print(json.dumps(h, ensure_ascii=False))
elif isinstance(recs, dict):
    if "KR0032" in recs:
        print(json.dumps(recs["KR0032"], ensure_ascii=False, indent=2))
    else:
        print("keys sample:", list(recs.keys())[:10])
