#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""All calibration evidence entries of one filing (pdf quarter) of one company, over every concept (read-only).
   usage: bspl_followup_filing_evidence.py KR0049 2026.2Q"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
code, q = sys.argv[1], sys.argv[2]
d = json.loads((ROOT / f"data/_derived/bspl_granularity_20261011/candidates/{code}.json").read_text(encoding="utf-8"))
for ck, cv in sorted(d["calibration"].items()):
    for e in cv["evidence"]:
        if e[0] == q:
            print(f"{ck:<42} {cv['status']:<9} {e[1]} col{e[2]} {e[3]:<7} ok={e[4]!s:<5} obs={e[5]:,.2f} anchor={e[6]:,.2f}")
