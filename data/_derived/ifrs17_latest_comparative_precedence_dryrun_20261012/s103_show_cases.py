"""Read-only: review case_verdicts.csv.  usage: python s103_show_cases.py [inv|census] """
from __future__ import annotations

import csv
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(HERE / "case_verdicts.csv", encoding="utf-8-sig")))
mode = sys.argv[1] if len(sys.argv) > 1 else "inv"
for r in rows:
    if mode == "inv" and not r["inventory_id"]:
        continue
    if mode == "census" and r["inventory_id"]:
        continue
    print(f"{r['case_id']:<11} {r['inventory_id']:<9} {r['domain'][:13]:<13} {r['code']} {r['company'][:7]:<7} {r['quarters'][:22]:<22} t:{r['type_original']}->{r['type_after_dryrun']} | {r['verdict'][:58]} | chg {r['cells_changed']} fill {r['cells_filled']} | gold {r['gold_conflict']}")
