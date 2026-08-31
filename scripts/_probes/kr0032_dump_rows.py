# -*- coding: utf-8 -*-
"""Dump KR0032 rows from kics_disclosure.json for recent quarters, items 1-46."""
import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0032"]
quarters = sorted(set(r["공시분기"] for r in rows))
print(f"KR0032 rows total: {len(rows)}; quarters: {quarters}")

target_quarters = ["2025.2Q", "2025.4Q", "2026.1Q", "2026.2Q"]
for q in target_quarters:
    qrows = sorted([r for r in rows if r["공시분기"] == q], key=lambda r: r["항목번호"])
    print(f"\n===== {q} ({len(qrows)} rows) =====")
    for r in qrows:
        v = r.get("값")
        vp = r.get("값_적용후", "<MISSING KEY>")
        print(f"  item{r['항목번호']:>3} {r['항목명']!r:45s} 값={v!r:>15} 값_적용후={vp!r}")
