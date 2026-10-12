"""Read-only: summarise exceptions_inventory.csv (counts by domain/status/type; list of type A and cross-filing candidate rows)."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(HERE / "exceptions_inventory.csv", encoding="utf-8-sig")))
print("rows", len(rows))
print("by domain x type:")
c = Counter((r["domain"], r["type"]) for r in rows)
for k in sorted(c):
    print("  ", k, c[k])
print("by status x type:")
c = Counter((r["status"], r["type"]) for r in rows)
for k in sorted(c):
    print("  ", k, c[k])
mode = sys.argv[1] if len(sys.argv) > 1 else "A"
print("-" * 100)
for r in rows:
    if mode == "A" and r["type"] != "A":
        continue
    if mode == "X" and r["cross_filing_candidate"] != "Y":
        continue
    print(f"{r['id']} {r['domain'][:14]:<14} {r['code']} {r['company'][:8]:<8} {r['quarters'][:34]:<34} n={r['n_cells']:<4} {r['rule'][:34]:<34} [{r['status']}] t={r['type']} cf={r['cross_filing_candidate']} pr={r['prior_round']}")
