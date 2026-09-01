"""Break the PL coverage census down by filing cadence, and drill into the short companies."""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
CEN = json.loads((ROOT / "data" / "_derived" / "pl_coverage_census_20260901.json").read_text(encoding="utf-8"))
QUARTERS = CEN["quarters"]
ANNUAL = [q for q in QUARTERS if q.endswith("4Q")]
INTERIM = [q for q in QUARTERS if not q.endswith("4Q")]

grid = CEN["grid"]
pc = CEN["per_company"]

print("annual quarters in window:", ANNUAL)
print("interim quarters in window:", INTERIM)
print()

# tally split by cadence
t = collections.Counter()
for code, row in grid.items():
    for q, cell in row.items():
        t[(("ANNUAL" if q.endswith("4Q") else "INTERIM"), cell["verdict"])] += 1
for k in sorted(t):
    print(f"  {k[0]:8s} {k[1]:24s} {t[k]:5d}")
print()

# Companies whose ONLY master coverage is annual quarters
print("=== companies with zero interim coverage in master (annual-only pattern) ===")
print(f"{'code':7s} {'name':24s} {'annual_in_mst':>13s} {'annual_missing':>15s}  {'interim_raw_dirs':>16s}")
annual_only = []
for code in sorted(grid):
    row = grid[code]
    n_int = sum(1 for q in INTERIM if row[q]["verdict"] == "a_in_master")
    n_ann = sum(1 for q in ANNUAL if row[q]["verdict"] == "a_in_master")
    if n_int == 0:
        annual_only.append(code)
        miss = [q for q in ANNUAL if row[q]["verdict"] != "a_in_master"]
        int_raw = [q for q in INTERIM if row[q]["raw"] is not None and not row[q]["raw"]["no_filing"]]
        print(
            f"{code:7s} {pc[code]['name'][:24]:24s} {n_ann:13d} {','.join(miss) or '-':>15s}  "
            f"{','.join(int_raw) or '-':>16s}"
        )
print()

# For those, what does the raw layer say about the MISSING annual quarters?
print("=== missing ANNUAL cells for the annual-only companies: raw-layer verdict ===")
for code in annual_only:
    row = grid[code]
    for q in ANNUAL:
        if row[q]["verdict"] != "a_in_master":
            r = row[q]["raw"]
            print(f"{code:7s} {pc[code]['name'][:20]:20s} {q}  verdict={row[q]['verdict']:22s} raw={r}")
print()

print("=== the 5 b_raw_no_pl cells (raw on disk, no PL rows) ===")
for code in sorted(grid):
    for q in QUARTERS:
        cell = grid[code][q]
        if cell["verdict"] == "b_raw_no_pl":
            print(f"{code:7s} {pc[code]['name'][:20]:20s} {q}  raw={json.dumps(cell['raw'], ensure_ascii=False)}")
print()

print("=== unknown codes present in raw but absent from master ===")
for code in sorted(grid):
    if pc[code]["n_quarters_in_master"] == 0:
        qs = [(q, grid[code][q]["raw"]) for q in QUARTERS if grid[code][q]["raw"]]
        print(f"{code}: {len(qs)} raw dirs")
        for q, r in qs:
            print(f"    {q} {r['dir']} kind={r['report_kind']} no_filing={r['no_filing']} n_xml={r['n_xml']}")
