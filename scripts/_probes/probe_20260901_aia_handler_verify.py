"""Run the live AIA handler + assemble() on every AIA year, and diff 2025.4Q against the
committed master to prove the already-reviewed cells did not move."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from scripts.build_pl_breakdown import (  # noqa: E402
    ITEM_NAMES, ZERO_FILL_ITEMS, assemble, discover_filings, parse_filing,
)

CODE = "KR0080"
filings = discover_filings()[CODE]

parsed = {}
for q in sorted(filings):
    t1, t2 = parse_filing(filings[q], True, code=CODE, name="에이아이에이생명보험", quarter=q)
    parsed[q] = (t1, t2)
    print(f"{q}: t1={'None' if t1 is None else 'dict'}  "
          f"t2_keys={sorted(k for k in (t2 or {}) if isinstance(k, int))}")

# reproduce main()'s two-pass zero_fill logic
ever = set()
for q, (t1, t2) in parsed.items():
    if t1 is None and t2 is None:
        continue
    probe = assemble(t1, t2, True, zero_fill_ok=frozenset())
    for n in ZERO_FILL_ITEMS:
        if probe[n] is not None:
            ever.add(n)
zero_fill_ok = ZERO_FILL_ITEMS - ever
print(f"\never_extracted={sorted(ever)}  zero_fill_ok={sorted(zero_fill_ok)}\n")

vecs = {}
for q in sorted(parsed):
    t1, t2 = parsed[q]
    if t1 is None and t2 is None:
        print(f"--- {q}: NO DATA")
        continue
    v = assemble(t1, t2, True, zero_fill_ok=zero_fill_ok)
    vecs[q] = v
    print(f"--- {q}")
    for n in range(1, 25):
        print(f"    item{n:>2} {ITEM_NAMES[n][:20]:20s} {v[n]}")

# regression check against the committed master
recs = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
committed = {}
for r in recs:
    if r["원보험사코드"] == CODE and isinstance(r["항목번호"], int) and r["항목번호"] <= 24:
        committed.setdefault(r["공시분기"], {})[r["항목번호"]] = r["값"]

print("\n=== regression vs committed master ===")
for q, cm in sorted(committed.items()):
    v = vecs.get(q)
    if v is None:
        print(f"  {q}: builder now produces NOTHING (was committed!) *** REGRESSION ***")
        continue
    drift = []
    for n in range(1, 25):
        a, b = cm.get(n), (round(v[n], 6) if isinstance(v[n], float) else v[n])
        if a != b:
            drift.append(f"item{n}: {a} -> {b}")
    print(f"  {q}: {'NO DRIFT' if not drift else 'DRIFT ' + str(len(drift))}")
    for d in drift:
        print("      " + d)

print("\n=== newly filled quarters ===")
for q in sorted(vecs):
    if q not in committed:
        n_val = sum(1 for n in range(1, 25) if vecs[q][n] is not None)
        print(f"  {q}: {n_val}/24 core items non-null")
