#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
rows = json.loads((ROOT / "data/_derived/bspl_followup_20261011/item10_tag_scan.json").read_text(encoding="utf-8"))
c = Counter(); tot = Counter()
for r in rows:
    tot[r["code"]] += 1
    if r.get("master_equals_dep") and not r.get("master_equals_cash"):
        c[r["code"]] += 1
print("rows", len(rows), "by company (dep-not-cash):", dict(c), "total scanned per company:", dict(tot))
