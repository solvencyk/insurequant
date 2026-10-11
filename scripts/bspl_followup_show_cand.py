#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print raw candidate dicts of one company/item/quarter (read-only).  usage: bspl_followup_show_cand.py KR1104 3 2025.3Q"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
code, item, q = sys.argv[1], int(sys.argv[2]), sys.argv[3]
d = json.loads((ROOT / f"data/_derived/bspl_granularity_20261011/candidates/{code}.json").read_text(encoding="utf-8"))
for c in d["candidates"]:
    if c["item"] == item and c["quarter"] == q:
        print(json.dumps(c, ensure_ascii=False, indent=1))
