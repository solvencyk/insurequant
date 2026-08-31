# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0074" and r.get("공시분기") == "2026.2Q"]
print(f"2026.2Q rows: {len(rows)}")
for r in sorted(rows, key=lambda x: x.get("항목번호", 0)):
    print(f"  item{r.get('항목번호')}: {r.get('항목명')!r} 값={r.get('값')} 값_적용후={r.get('값_적용후', 'MISSING_KEY')}")

print()
rows1q = [r for r in data if r.get("원보험사코드") == "KR0074" and r.get("공시분기") == "2026.1Q"]
print(f"2026.1Q rows: {len(rows1q)}")
for r in sorted(rows1q, key=lambda x: x.get("항목번호", 0)):
    print(f"  item{r.get('항목번호')}: {r.get('항목명')!r} 값={r.get('값')} 값_적용후={r.get('값_적용후', 'MISSING_KEY')}")
