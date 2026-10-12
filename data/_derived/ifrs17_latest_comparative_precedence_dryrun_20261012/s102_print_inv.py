"""Read-only: print full inventory rows for given ids.  usage: python s102_print_inv.py INV-0253 INV-0276 ..."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
rows = {r["id"]: r for r in csv.DictReader(open(HERE / "exceptions_inventory.csv", encoding="utf-8-sig"))}
for i in sys.argv[1:]:
    r = rows[i]
    print("=" * 90)
    for k, v in r.items():
        print(f"  {k}: {v}")
