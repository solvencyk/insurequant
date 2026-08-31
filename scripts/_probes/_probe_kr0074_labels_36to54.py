# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0074"]
target_items = list(range(36, 55))
labels = {}
for r in rows:
    n = r.get("항목번호")
    if n in target_items and n not in labels:
        labels[n] = (r.get("항목명"), r.get("공시분기"))

for n in target_items:
    if n in labels:
        print(f"item{n}: {labels[n][0]!r}  (from {labels[n][1]})")
    else:
        print(f"item{n}: NEVER SEEN for KR0074")

print()
print("=== full history of items 36-46 across quarters (values) ===")
for n in range(36, 47):
    print(f"--- item{n} ---")
    hist = sorted([r for r in rows if r.get("항목번호")==n], key=lambda x: x.get("공시분기"))
    for r in hist:
        print(f"  {r.get('공시분기')}: 값={r.get('값')} 값_적용후={r.get('값_적용후','MISSING')}")
