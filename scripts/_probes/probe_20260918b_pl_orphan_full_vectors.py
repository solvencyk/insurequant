# -*- coding: utf-8 -*-
"""Dump the full 24-item vector for each of the 29 orphan-parent buckets."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "PL_breakdown.json", encoding="utf-8") as fh:
    rows = json.load(fh)

buckets = {}
meta = {}
for r in rows:
    key = (r["원보험사코드"], r["공시분기"])
    buckets.setdefault(key, {})[r["항목번호"]] = r["값"]
    meta[r["원보험사코드"]] = (r["원수사명"], r["생손보여부"])

CHILDREN = list(range(3, 13))
orphans = []
for key, items in sorted(buckets.items()):
    if items.get(2) is not None:
        continue
    if not any(items.get(n) is not None for n in CHILDREN):
        continue
    orphans.append(key)

for key in orphans:
    code, q = key
    name, kind = meta[code]
    items = buckets[key]
    print(f"=== {code} {name} ({kind}) {q} ===")
    parts = []
    for n in range(1, 25):
        v = items.get(n)
        parts.append(f"{n}={'None' if v is None else format(v, '.3f')}")
    print("  " + " | ".join(parts[:12]))
    print("  " + " | ".join(parts[12:]))
    print()
