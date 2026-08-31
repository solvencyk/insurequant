# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
with open("kics_rate_sensitivity.json", "r", encoding="utf-8") as f:
    data = json.load(f)
rows = [r for r in data if r["원보험사코드"]=="KR0010" and r["공시분기"]=="2026.2Q"]
print(f"{len(rows)} rows")
for r in rows:
    print(json.dumps(r, ensure_ascii=False))
