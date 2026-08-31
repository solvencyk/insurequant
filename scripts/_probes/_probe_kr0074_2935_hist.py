# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0074"]

for n in range(29, 36):
    print(f"--- item{n} ---")
    hist = sorted([r for r in rows if r.get("항목번호")==n], key=lambda x: x.get("공시분기"))
    for r in hist:
        match = "OK" if str(r.get('값'))==str(r.get('값_적용후')) else "DIFF"
        print(f"  {r.get('공시분기')}: 값={r.get('값')} 값_적용후={r.get('값_적용후','MISSING')} [{match}]")

print()
print("--- items 4-13 mirror check across ALL quarters ---")
for n in range(4, 14):
    hist = sorted([r for r in rows if r.get("항목번호")==n], key=lambda x: x.get("공시분기"))
    mismatches = [h for h in hist if str(h.get('값')) != str(h.get('값_적용후', 'MISSING'))]
    print(f"item{n}: {len(hist)} quarters total, {len(mismatches)} mismatched/missing 값_적용후")
    for m in mismatches:
        print(f"    {m.get('공시분기')}: 값={m.get('값')} 값_적용후={m.get('값_적용후','MISSING')}")
