# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ta = json.load(open("data/_derived/kics_transition_applicability.json", encoding="utf-8"))
print(type(ta), len(ta) if hasattr(ta,'__len__') else '?')
# print first few keys
if isinstance(ta, dict):
    keys = list(ta.keys())
    print("sample keys:", keys[:5])
    for k in keys:
        if "KR0076" in k:
            print(k, "->", ta[k])
