#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
o = json.loads((ROOT / "data/_derived/bspl_followup_20261011/pl_item1_holds.json").read_text(encoding="utf-8"))
for r in o:
    legs = ", ".join(f"{k}={'None' if v is None else f'{v:,.1f}'}" for k, v in r["legs"].items())
    neigh = r["neighbour_legs_present(2,13,14)"]
    ns = " ".join(f"{q[2:]}:{''.join('1' if x else '0' for x in v)}" for q, v in neigh.items())
    print(f"{r['key']:<16} {r['company'][:8]:<8} cand={r['candidate_mn']:>11,.1f} | {legs} | xlob={r['extra_lob_sum']:,.0f} oe={r['기타사업비용']} | res={r['residual_if_loaded']:,.1f} {r['lineage']}")
    print(f"     legs(2,13,14) present by quarter: {ns}")
