# -*- coding: utf-8 -*-
"""Dump items 1-3/14/47-51 for the 3-company/6-quarter backlog (KR1098/KR0097/KR0071)."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

TARGETS = [
    ("KR1098", "2024.2Q"), ("KR1098", "2024.3Q"), ("KR1098", "2024.4Q"),
    ("KR0097", "2024.2Q"), ("KR0097", "2024.4Q"),
    ("KR0071", "2024.4Q"),
]

by_cq = {}
for r in data:
    c, q = r.get("원보험사코드"), r.get("공시분기")
    by_cq.setdefault((c, q), {})[int(r["항목번호"])] = r

for c, q in TARGETS:
    items = by_cq.get((c, q), {})
    print(f"\n=== {c} {q}  (row exists: {bool(items)}, n_items={len(items)}) ===")
    if not items:
        print("  NO ROWS AT ALL for this (company,quarter)")
        continue
    for it in (1, 2, 3, 14, 47, 48, 49, 50, 51):
        r = items.get(it)
        if r is None:
            print(f"  item{it:>2}: (absent)")
        else:
            print(f"  item{it:>2} [{r.get('항목명')}]: 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r}")
