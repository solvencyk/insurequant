# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = json.load(open("kics_disclosure.json", encoding="utf-8"))
rows = [r for r in data if r.get("원보험사코드") == "KR0079"]

for q in ("2025.4Q", "2026.1Q", "2026.2Q"):
    print(f"===== {q} =====")
    qrows = sorted([r for r in rows if r["공시분기"] == q], key=lambda r: r["항목번호"])
    for r in qrows:
        v = r.get("값")
        vp = r.get("값_적용후", "<absent>")
        print(f"  item{r['항목번호']:>2} | {r['항목명']!r:60s} | 값={v!r} | 값_적용후={vp!r}")
