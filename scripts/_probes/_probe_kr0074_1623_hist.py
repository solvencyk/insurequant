# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0074"]
for n in range(16, 24):
    hist = sorted([r for r in rows if r.get("항목번호")==n], key=lambda x: x.get("공시분기"))
    mismatches = [h for h in hist if str(h.get('값')) != str(h.get('값_적용후', 'MISSING')) and h.get('공시분기')!='2026.2Q']
    print(f"item{n}: {len(hist)} quarters, label={hist[0].get('항목명')!r}, non-2026.2Q mismatches={len(mismatches)}")
    for m in mismatches:
        print(f"    ANOMALY {m.get('공시분기')}: 값={m.get('값')} 값_적용후={m.get('값_적용후')}")
