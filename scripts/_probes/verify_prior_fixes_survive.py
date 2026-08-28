import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

rows = json.load(open("PL_breakdown.json", encoding="utf-8"))
idx = {}
for r in rows:
    idx[(r["원보험사코드"], r["항목번호"], r["공시분기"])] = r["값"]

print("=== KR0083 2024.3Q (gold override, expect item27~-265227, item28~-5322, item30~-537 백만원) ===")
for item in (27, 28, 30):
    v = idx.get(("KR0083", item, "2024.3Q"))
    print(f"  item{item}: {v}  (억원: {v/100 if v is not None else None})")

print("\n=== KR0032 2026.2Q (예실차, expect item6~-10200, item7~-79700 백만원 [당분기]) ===")
rows_by_key = {}
for r in rows:
    rows_by_key[(r["원보험사코드"], r["항목번호"], r["공시분기"])] = r
for item in (6, 7):
    r = rows_by_key.get(("KR0032", item, "2026.2Q"))
    if r:
        print(f"  item{item}: 값(YTD)={r['값']}  값_당분기={r.get('값_당분기')}  "
              f"(당분기 억원: {r.get('값_당분기')/100 if r.get('값_당분기') is not None else None})")
    else:
        print(f"  item{item}: ROW MISSING")
