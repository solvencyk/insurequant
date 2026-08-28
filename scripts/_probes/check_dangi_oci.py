#!/usr/bin/env python3
"""Check 값_당분기 got populated for items 25-31 in root PL_breakdown.json, and sanity-check
Q1 == YTD, and a QoQ-derived value against a company we probed directly via tier1_for()."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

d = json.loads(Path("PL_breakdown.json").read_text(encoding="utf-8"))
idx = {}
for r in d:
    idx[(r["원보험사코드"], r["항목번호"], r["공시분기"])] = r

samples = [
    ("KR0008", 25, "2024.1Q"), ("KR0008", 25, "2024.2Q"), ("KR0008", 25, "2024.3Q"),
    ("KR0008", 31, "2026.2Q"), ("KR0069", 25, "2023.4Q"), ("KR0069", 25, "2024.4Q"),
    ("KR0073", 28, "2025.4Q"),
]
for code, item, q in samples:
    r = idx.get((code, item, q))
    if r is None:
        print(f"{code} item{item} {q}: MISSING ROW")
        continue
    print(f"{code} item{item} {q}: 값(YTD)={r.get('값')}  값_당분기={r.get('값_당분기')}")

# does every item-25..31 row have the 값_당분기 KEY present (even if null)?
missing_key = [ (r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in d
                if r["항목번호"] in (25,26,27,28,29,30,31) and "값_당분기" not in r ]
print(f"\nOCI-item rows missing the 값_당분기 KEY entirely: {len(missing_key)}")
print(missing_key[:10])

n_val = sum(1 for r in d if r["항목번호"] in (25,26,27,28,29,30,31) and r.get("값") is not None)
n_dangi = sum(1 for r in d if r["항목번호"] in (25,26,27,28,29,30,31) and r.get("값_당분기") is not None)
n_total = sum(1 for r in d if r["항목번호"] in (25,26,27,28,29,30,31))
print(f"\nOCI rows total={n_total}  값 populated={n_val}  값_당분기 populated={n_dangi}")
