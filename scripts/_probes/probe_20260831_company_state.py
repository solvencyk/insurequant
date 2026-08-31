# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if isinstance(data, dict) and "records" in data:
    records = data["records"]
else:
    records = data

print("total records:", len(records))
print("sample record keys:", list(records[0].keys()) if records else None)

targets = ["KR0009", "KR0150", "KR0087", "KR0083", "KR1011", "KR0051", "KR0079"]
period = "2026.2Q"

for code in targets:
    rows = [r for r in records if r.get("원보험사코드") == code and r.get("공시분기") == period]
    print(f"\n=== {code} {period}: {len(rows)} rows ===")
    rows_sorted = sorted(rows, key=lambda r: (r.get("항목번호") if isinstance(r.get("항목번호"), int) else 999))
    for r in rows_sorted:
        print(f"  item{r.get('항목번호')!s:>4} | {r.get('항목명','')[:40]:40s} | 값={r.get('값')!r} | 값_적용후={r.get('값_적용후')!r}")
