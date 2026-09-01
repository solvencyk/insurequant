"""What status did the PL builder record for the 16 b_raw_no_pl cells?"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

cov = json.loads((ROOT / "data" / "_derived" / "pl_breakdown_coverage.json").read_text(encoding="utf-8"))
CEN = json.loads((ROOT / "data" / "_derived" / "pl_coverage_census_20260901.json").read_text(encoding="utf-8"))
grid, pc = CEN["grid"], CEN["per_company"]

by = {(c["code"], c["quarter"]): c for c in cov}
print(f"coverage rows = {len(cov)}")

import collections
st = collections.Counter(c["status"] for c in cov)
print("status tally:", dict(st))
print()

print("=== coverage status for each b_raw_no_pl cell ===")
targets = []
for code in sorted(grid):
    for q, cell in grid[code].items():
        if cell["verdict"] == "b_raw_no_pl":
            targets.append((code, q))
targets.sort()
for code, q in targets:
    c = by.get((code, q))
    nm = pc[code]["name"]
    if c is None:
        print(f"{code:7s} {nm[:20]:20s} {q}  *** NOT IN COVERAGE AT ALL ***")
    else:
        print(f"{code:7s} {nm[:20]:20s} {q}  status={c['status']:22s} tier2={c['tier2']}")

print()
print("=== all coverage rows with status raw_not_extracted / no_income_statement ===")
for c in cov:
    if c["status"] in ("raw_not_extracted", "no_income_statement"):
        print(f"  {c['code']:7s} {c['name'][:20]:20s} {c['quarter']}  {c['status']}")
