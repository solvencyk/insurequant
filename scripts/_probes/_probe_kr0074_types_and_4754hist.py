# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0074"]

# check raw JSON types for a sample row (2026.2Q item1)
sample = [r for r in rows if r.get("공시분기")=="2026.2Q" and r.get("항목번호")==1][0]
print("sample item1 2026.2Q raw dict:", json.dumps(sample, ensure_ascii=False))
print("type of 값:", type(sample.get("값")))
print("type of 값_적용후:", type(sample.get("값_적용후")))

print()
for n in range(47, 55):
    print(f"--- item{n} ---")
    hist = sorted([r for r in rows if r.get("항목번호")==n], key=lambda x: x.get("공시분기"))
    for r in hist:
        print(f"  {r.get('공시분기')}: 값={r.get('값')!r} 값_적용후={r.get('값_적용후','MISSING')!r}")
