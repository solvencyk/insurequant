# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    rows = json.load(f)

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
    matches = [r for r in rows if r.get("원보험사코드") == company and r.get("공시분기") == quarter and r.get("항목번호") in want_items]
    matches.sort(key=lambda r: r.get("항목번호", 0))
    for r in matches:
        label = r.get("항목명","")
        print(f"  item{r.get('항목번호'):>3} {label[:28]:28s} val={r.get('값')!r:>14} post={r.get('값_적용후')!r:>14}")
    print()
