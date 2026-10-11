#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print all calibration evidence of one concept key.  usage: bspl_followup_concept_evidence.py KR1011 "13:AC_CHILDREN[ac_children]|K" """
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
code, key = sys.argv[1], sys.argv[2]
d = json.loads((ROOT / f"data/_derived/bspl_granularity_20261011/candidates/{code}.json").read_text(encoding="utf-8"))
cv = d["calibration"].get(key)
print(key, cv["status"] if cv else None)
for e in (cv or {}).get("evidence", []):
    print(f"  filing {e[0]} period {e[1]} col{e[2]} {e[3]:<7} ok={e[4]!s:<5} obs={e[5]:,.1f} anchor={e[6]:,.1f}")
