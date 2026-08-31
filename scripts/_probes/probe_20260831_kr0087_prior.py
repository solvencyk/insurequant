# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)
records = data["records"] if isinstance(data, dict) and "records" in data else data

for period in ("2025.4Q", "2026.1Q"):
    rows = [r for r in records if r.get("원보험사코드") == "KR0087" and r.get("공시분기") == period]
    rows_sorted = sorted(rows, key=lambda r: r.get("항목번호") if isinstance(r.get("항목번호"), int) else 999)
    print(f"=== KR0087 {period}: {len(rows)} rows ===")
    for r in rows_sorted:
        if isinstance(r.get('항목번호'), int) and 1 <= r['항목번호'] <= 28:
            print(f"  item{r['항목번호']:>3} | {r['항목명'][:35]:35s} | 값={r.get('값')!r}")
