# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    rows = json.load(f)

print(f"total_rows={len(rows)}")

kr1000_2026q2 = [r for r in rows if r.get("원보험사코드") == "KR1000" and r.get("공시분기") == "2026.2Q"]
print(f"\n=== KR1000 2026.2Q rows: {len(kr1000_2026q2)} ===")
for r in sorted(kr1000_2026q2, key=lambda x: x.get("항목번호", 0)):
    print(f"item{r.get('항목번호')}\t{r.get('항목명')!r}\t값={r.get('값')}\t값_적용후={r.get('값_적용후', 'MISSING_KEY')}")

print(f"\n=== KR1000 2025.4Q rows (label reference, full-form even-Q): ===")
kr1000_2025q4 = [r for r in rows if r.get("원보험사코드") == "KR1000" and r.get("공시분기") == "2025.4Q"]
for r in sorted(kr1000_2025q4, key=lambda x: x.get("항목번호", 0)):
    print(f"item{r.get('항목번호')}\t{r.get('항목명')!r}\t값={r.get('값')}\t값_적용후={r.get('값_적용후', 'MISSING_KEY')}")
