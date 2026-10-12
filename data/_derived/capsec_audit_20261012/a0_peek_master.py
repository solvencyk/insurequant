# -*- coding: utf-8 -*-
"""a0: peek at kics_disclosure.json structure (read-only). Audit 20261012."""
import json
import sys
from collections import Counter

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
d = json.load(open(ROOT + "/kics_disclosure.json", encoding="utf-8"))
print("n records", len(d))
print("keys of first", list(d[0].keys()))
print("first", json.dumps(d[0], ensure_ascii=False))
qs = Counter(r.get("공시분기") for r in d)
print("quarters", sorted(qs.items())[-8:])
# items in 2026.2Q
items = {}
for r in d:
    if r.get("공시분기") == "2026.2Q":
        items.setdefault(r.get("항목번호"), set()).add(r.get("항목명"))
for k in sorted(items, key=lambda x: (x is None, x)):
    print(k, sorted(items[k]))
codes = sorted({(r.get("원보험사코드"), r.get("원수사명")) for r in d if r.get("공시분기") == "2026.2Q"})
print(len(codes), codes)
