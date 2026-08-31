# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0010"]
print(f"total KR0010 rows: {len(rows)}")
quarters = sorted(set(r["공시분기"] for r in rows))
print("quarters present:", quarters)

for q in quarters:
    qrows = sorted([r for r in rows if r["공시분기"] == q], key=lambda r: r["항목번호"])
    print(f"\n=== {q} ({len(qrows)} rows) ===")
    for r in qrows:
        v2 = r.get("값_적용후", None)
        print(f"  item{r['항목번호']:>3} {r['항목명']!r:40s} 값={r['값']!r} 값_적용후={v2!r}")
