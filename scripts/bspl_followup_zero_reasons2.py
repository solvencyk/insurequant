#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
rows = json.loads((ROOT / "data/_derived/bspl_followup_20261011/zero_proof_report.json").read_text(encoding="utf-8"))
v = Counter(r["verdict"] for r in rows)
print(dict(v))
tok = Counter()
for r in rows:
    if r["verdict"] != "KEEP_HELD":
        continue
    for z in ("Z1", "Z2", "Z3", "Z4", "Z5", "Z6"):
        if f"{z}:" in (r.get("reason") or ""):
            tok[z] += 1
print("KEEP_HELD cells mentioning each rule:", dict(tok))
