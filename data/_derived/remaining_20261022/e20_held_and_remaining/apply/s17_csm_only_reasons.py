#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 17: reasons the 10 CSM-only buckets of d_census_addl.csv are left (closure_basis / disposition_reason) -> s17_csm_only_reasons.txt (read-only)"""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
D = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census/d_census_addl.csv")
with open(D, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
L = []
for r in rows:
    if r["scope"] != "ADDL_CSM_ONLY":
        continue
    L.append(f"{r['code']} {r['company']} {r['quarter']} | closes={r['latest_vector_closes_block']} | csm_items={r['csm_items_differ'][:60]} | gold={r['gold_cells'][:80]}")
    L.append(f"     closure_basis: {r['closure_basis'][:700]}")
    L.append(f"     disposition_reason: {r['disposition_reason'][:500]}")
(HERE / "s17_csm_only_reasons.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
print("\n".join(L))
