# -*- coding: utf-8 -*-
"""Reconstruct the coordinator's master-wide item48 == item14(pre)*0.5 sweep."""
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

by_bucket = {}
for r in rows:
    key = (r["원보험사코드"], r["공시분기"])
    by_bucket.setdefault(key, {})[r["항목번호"]] = r

TOL = 2.0
match = 0
mismatch = 0
missing = 0
mismatches = []
for key, items in sorted(by_bucket.items()):
    i48 = items.get(48, {}).get("값")
    i14 = items.get(14, {}).get("값")
    i3 = items.get(3, {}).get("값")
    if i48 is None or i14 is None:
        missing += 1
        continue
    try:
        i48f = float(i48)
        i14f = float(i14)
    except (TypeError, ValueError):
        missing += 1
        continue
    expected = i14f * 0.5
    diff = i48f - expected
    if abs(diff) <= TOL:
        match += 1
    else:
        mismatch += 1
        i3f = None
        eq_item3 = False
        if i3 is not None:
            try:
                i3f = float(i3)
                eq_item3 = abs(i48f - i3f) < 1e-6
            except (TypeError, ValueError):
                pass
        mismatches.append((key[0], key[1], i48f, i14f, expected, diff, i3f, eq_item3))

print(f"match={match} mismatch={mismatch} missing_input={missing}")
print(f"of mismatches, item48==item3: {sum(1 for m in mismatches if m[7])}")
print()
print(f"{'code':8s} {'quarter':9s} {'item48':>12s} {'item14':>12s} {'expected':>12s} {'diff':>10s} {'item3':>12s} eq3")
for m in sorted(mismatches, key=lambda x: (x[0], x[1])):
    print(f"{m[0]:8s} {m[1]:9s} {m[2]:>12.2f} {m[3]:>12.2f} {m[4]:>12.2f} {m[5]:>10.2f} {str(m[6]):>12s} {m[7]}")
