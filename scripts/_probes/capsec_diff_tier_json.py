# -*- coding: utf-8 -*-
"""Diff two kics_tier{1,2}_utilization.json snapshots at the top level per-company, printing
every changed field. Used to confirm utilization_pct is UNCHANGED (restored) while
numerator_as_of / comment fields ARE allowed to change."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
before = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
after = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))


def rows(d):
    for key in ("results", "companies", "data"):
        if key in d and isinstance(d[key], list):
            return d[key]
    raise KeyError(f"no row list found, top keys={list(d.keys())}")


b_rows, a_rows = rows(before), rows(after)
b_by = {r.get("code"): r for r in b_rows}
a_by = {r.get("code"): r for r in a_rows}
assert set(b_by) == set(a_by), (set(b_by) ^ set(a_by))

util_changed = []
other_changed = []
for code in sorted(b_by):
    br, ar = b_by[code], a_by[code]
    keys = set(br) | set(ar)
    for k in sorted(keys):
        if br.get(k) != ar.get(k):
            if k in ("utilization_pct", "utilization_pct_strict"):
                util_changed.append((code, k, br.get(k), ar.get(k)))
            else:
                other_changed.append((code, k, br.get(k), ar.get(k)))

print(f"utilization_pct(_strict) changes: {len(util_changed)}")
for d in util_changed:
    print(f"  {d}")
print(f"\nother field changes: {len(other_changed)}")
for d in other_changed:
    print(f"  {d}")
