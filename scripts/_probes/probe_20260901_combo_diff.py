"""Strict before/after combo-diff for a PL master rebuild.

Two-layer check (cell loss is a TWO-layer failure in this repo: whole cells disappearing,
AND surviving cells having a field silently nulled):
  layer 1 - (company, quarter) presence
  layer 2 - (company, quarter, item) presence AND value equality, incl. non-null -> null

usage: probe_20260901_combo_diff.py <before.json> <after.json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def load(p):
    rows = json.loads(Path(p).read_text(encoding="utf-8"))
    cells, cq, names = {}, set(), {}
    for r in rows:
        k = (r["원보험사코드"], r["공시분기"], r["항목번호"])
        cells[k] = r.get("값")
        cq.add((r["원보험사코드"], r["공시분기"]))
        names[r["원보험사코드"]] = r["원수사명"]
    return rows, cells, cq, names


b_rows, b, b_cq, b_names = load(sys.argv[1])
a_rows, a, a_cq, a_names = load(sys.argv[2])
names = {**b_names, **a_names}

print(f"before: {len(b_rows)} rows, {len(b_cq)} company-quarters, {len(b)} cells")
print(f"after : {len(a_rows)} rows, {len(a_cq)} company-quarters, {len(a)} cells")

lost_cq = sorted(b_cq - a_cq)
new_cq = sorted(a_cq - b_cq)
print(f"\nLOST company-quarters: {len(lost_cq)}")
for c, q in lost_cq:
    print(f"   *** {c} {names.get(c)} {q}")
print(f"NEW  company-quarters: {len(new_cq)}")
for c, q in new_cq:
    n = sum(1 for (cc, qq, it), v in a.items() if cc == c and qq == q and v is not None)
    print(f"   +   {c} {names.get(c)} {q}   ({n} non-null cells)")

lost_cells = sorted(k for k in b if k not in a)
print(f"\nLOST cells (key gone): {len(lost_cells)}")
for k in lost_cells[:40]:
    print(f"   *** {k} was {b[k]}")

nulled = sorted(k for k in b if k in a and b[k] is not None and a[k] is None)
print(f"\nNULLED cells (value -> None): {len(nulled)}")
for k in nulled[:40]:
    print(f"   *** {k} was {b[k]}")

changed = sorted(k for k in b if k in a and b[k] is not None and a[k] is not None and b[k] != a[k])
print(f"\nCHANGED values: {len(changed)}")
for k in changed[:60]:
    print(f"   ~   {k}: {b[k]} -> {a[k]}")

added = sorted(k for k in a if k not in b)
add_cq = sorted({(c, q) for c, q, _ in added})
print(f"\nADDED cells: {len(added)}  across company-quarters: {add_cq}")

ok = not lost_cq and not lost_cells and not nulled and not changed
print(f"\nVERDICT: {'CLEAN (additive only)' if ok else '*** REGRESSION ***'}")
