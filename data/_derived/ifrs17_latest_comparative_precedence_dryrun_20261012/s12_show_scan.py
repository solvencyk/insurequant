"""Read-only: print the DIFF / NO_PRIOR rows of csm_prior_scan.csv compactly.

usage: python s12_show_scan.py [DIFF|NO_PRIOR|SAME|ALL]
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
want = sys.argv[1] if len(sys.argv) > 1 else "DIFF"
rows = list(csv.DictReader(open(HERE / "csm_prior_scan.csv", encoding="utf-8-sig")))
n = 0
for r in rows:
    if want != "ALL" and r["status"] != want:
        continue
    n += 1
    if want == "NO_PRIOR":
        print(f"{r['kr']} {r['name'][:8]:8s} later={r['later_q']} prior={r['prior_q']} blocks={r['n_prior_blocks']} src={r['src'][:60]}")
        continue
    p = [r[f"p{k}"] for k in range(1, 7)]
    m = [r[f"m{k}"] for k in range(1, 7)]
    print(f"{r['kr']} {r['name'][:8]:8s} later={r['later_q']} prior={r['prior_q']} items={r['diff_items']:7s} anchor={r['anchor'][:9] if r['anchor'] else '-':9s} src={r['src'][:32]}")
    print(f"      prior-col {p}")
    print(f"      master    {m}")
print("rows", n)
