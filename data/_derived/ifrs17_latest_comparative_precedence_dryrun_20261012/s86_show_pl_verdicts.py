"""Read-only: PL block verdict rows (pl_block_verdicts.csv) for company-quarters that carry a registered PL_BRIDGE baseline failure or are cross-filing candidates."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
pv = list(csv.DictReader(open(HERE / "pl_block_verdicts.csv", encoding="utf-8-sig")))
print("PL verdict rows", len(pv), dict(Counter(r["verdict"] for r in pv)))
inv = list(csv.DictReader(open(HERE / "exceptions_inventory.csv", encoding="utf-8-sig")))
keys = set()
for r in inv:
    if r["domain"].startswith("PL_breakdown") and r["rule"].startswith("PL_BRIDGE") and r["cross_filing_candidate"] == "Y":
        for q in r["quarters"].split("·"):
            keys.add((r["code"], q.strip()))
by = {(r["kr"], r["quarter"]): r for r in pv}
print("registered PL_BRIDGE cross-filing candidates:", len(keys))
for k in sorted(keys):
    r = by.get(k)
    if r is None:
        print(k, "NO PL VERDICT ROW")
        continue
    print(k[0], r["name"][:8], k[1], "| later", r["later_filing_q"], "| orig_fsapi", r["orig_fsapi"][:6], "| real", r["n_real_cells"], "items", r["real_items"], "| signflip", r["n_sign_flip_cells"], "| already_latest", r["n_already_latest"],
          "| t1 closed cur/lat", r["tier1_closed_current"], r["tier1_closed_latest"], "| baseline", r["bridge_baseline_current"], "| gold", r["gold_cells"], "|", r["verdict"])
