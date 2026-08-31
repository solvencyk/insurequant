# -*- coding: utf-8 -*-
"""Probe: kics_disclosure.json schema + item47-54 current census (read-only)."""
import io
import json
import sys
import collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "kics_disclosure.json", encoding="utf-8") as f:
    rows = json.load(f)

print("total rows", len(rows))
print("sample keys", list(rows[0].keys()))
print()

item_field = None
for k in rows[0].keys():
    if k in ("항목", "항목번호"):
        item_field = k
if item_field is None:
    # print raw repr of keys to spot mismatches
    print("keys repr:", [repr(k) for k in rows[0].keys()])

c = collections.Counter(r.get(item_field) for r in rows if item_field)
c47_54 = {k: v for k, v in c.items() if isinstance(k, int) and 47 <= k <= 54}
print("item47-54 row counts:", dict(sorted(c47_54.items())))
print()

# distinct 항목번호 values overall (sanity)
all_item_nos = sorted({k for k in c if isinstance(k, int)})
print("min item#", min(all_item_nos), "max item#", max(all_item_nos))
