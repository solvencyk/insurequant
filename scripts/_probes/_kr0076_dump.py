# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = json.load(open("kics_disclosure.json", encoding="utf-8"))
rows = [r for r in data if r.get("원보험사코드")=="KR0076" and r.get("공시분기")=="2026.2Q"]
rows.sort(key=lambda r: r.get("항목번호", 0))
print(f"n rows = {len(rows)}")
for r in rows:
    print(f"item{r.get('항목번호')!s:>3} | {r.get('항목명','')[:40]:40s} | 값={r.get('값')!r:>15} | 값_적용후={r.get('값_적용후', '<MISSING KEY>')!r}")
