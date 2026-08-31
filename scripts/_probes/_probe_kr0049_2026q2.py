# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0049" and r.get("공시분기") == "2026.2Q"]
for r in sorted(rows, key=lambda x: (x.get("항목번호") if x.get("항목번호") is not None else -1)):
    print(f"item{r.get('항목번호')!r:>5} {r.get('항목명','')!r:65s} 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r}")
