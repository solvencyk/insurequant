"""Split the (c) no-source cells into 'structurally normal' vs 'needs downloader'.

An annual-only filer having no Q1/Q2/Q3 source is NORMAL, not a gap.  What is NOT normal
is an ANNUAL (4Q) cell with no raw dir for a company that files annually.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
CEN = json.loads((ROOT / "data/_derived/pl_coverage_census_20260901.json").read_text(encoding="utf-8"))
grid, pc, QUARTERS = CEN["grid"], CEN["per_company"], CEN["quarters"]
ANNUAL = [q for q in QUARTERS if q.endswith("4Q")]
INTERIM = [q for q in QUARTERS if not q.endswith("4Q")]

# a company is "annual-only" if it has NO master coverage and NO live raw in any interim Q
annual_only = set()
for code in grid:
    if all(grid[code][q]["verdict"].startswith("c_") for q in INTERIM):
        annual_only.add(code)

t = collections.Counter()
needs_dl = []
for code in sorted(grid):
    for q in QUARTERS:
        v = grid[code][q]["verdict"]
        if not v.startswith("c_"):
            continue
        is_ann = q.endswith("4Q")
        if code in annual_only and not is_ann:
            t["c1_annual_only_filer_interim_quarter"] += 1
        elif is_ann:
            t["c2_ANNUAL_cell_with_no_raw"] += 1
            needs_dl.append((code, pc[code]["name"], q, v))
        else:
            t["c3_interim_absent_other"] += 1
            needs_dl.append((code, pc[code]["name"], q, v))

print(f"annual-only filers: {len(annual_only)} -> {sorted(annual_only)}")
print()
for k in sorted(t):
    print(f"  {k:42s} {t[k]:5d}")
print()
print("=== (c) cells that are NOT explained by the annual-only cadence ===")
for code, nm, q, v in needs_dl:
    print(f"  {code:7s} {str(nm)[:22]:22s} {q}  {v}")
print(f"  total: {len(needs_dl)}")

print()
print("=== per-company interim absence detail for the 'other' group ===")
others = sorted({c for c, _, _, _ in needs_dl} - annual_only)
for code in others:
    row = grid[code]
    miss = [q for q in QUARTERS if row[q]["verdict"].startswith("c_")]
    have = [q for q in QUARTERS if row[q]["verdict"] == "a_in_master"]
    print(f"  {code} {pc[code]['name']}: missing={miss}")
    print(f"      has={have}")
