# -*- coding: utf-8 -*-
"""Compare master kics_disclosure.json values against the raw-confirmed numbers for the 5 buckets."""
import sys
import io
import json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = data["rows"] if isinstance(data, dict) and "rows" in data else data

targets = [
    ("KR0075", "2024.4Q"),
    ("KR0075", "2025.1Q"),
    ("KR0087", "2025.2Q"),
    ("KR0068", "2025.2Q"),
    ("KR0004", "2025.1Q"),
]

want_items = {1,2,3,4,12,13,14,47,48,49,50,51}

for company, quarter in targets:
    print(f"=== {company} {quarter} ===")
    matches = [r for r in rows if r.get("company") == company and r.get("quarter") == quarter and r.get("item_no") in want_items]
    matches.sort(key=lambda r: r.get("item_no", 0))
    for r in matches:
        print(f"  item{r.get('item_no')} {r.get('item_label','')[:30]:30s} val={r.get('value')!r:>16} post={r.get('value_post')!r:>16}")
    print()
