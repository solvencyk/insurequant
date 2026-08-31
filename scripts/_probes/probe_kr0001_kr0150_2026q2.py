# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def rows_for(code, quarter):
    return [r for r in data if r.get("원보험사코드") == code and r.get("공시분기") == quarter]

for code in ("KR0001", "KR0150"):
    print(f"=== {code} ===")
    for q in ("2026.1Q", "2026.2Q"):
        rs = rows_for(code, q)
        print(f"  {q}: {len(rs)} rows")
        for r in sorted(rs, key=lambda x: x.get("항목번호", 0)):
            print(f"    item{r.get('항목번호')} {r.get('항목명')!r} = {r.get('값')} (적용후={r.get('값_적용후')})")
