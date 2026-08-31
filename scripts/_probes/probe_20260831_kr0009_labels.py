# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)
records = data["records"] if isinstance(data, dict) and "records" in data else data

# grab KR0009 2026.1Q rows for items 1-28 to copy labels + meta fields
rows = [r for r in records if r.get("원보험사코드") == "KR0009" and r.get("공시분기") == "2026.1Q"]
rows_sorted = sorted(rows, key=lambda r: r.get("항목번호") if isinstance(r.get("항목번호"), int) else 999)
print("KR0009 2026.1Q rows:", len(rows))
for r in rows_sorted:
    if isinstance(r.get("항목번호"), int) and 1 <= r["항목번호"] <= 28:
        print(json.dumps(r, ensure_ascii=False))
