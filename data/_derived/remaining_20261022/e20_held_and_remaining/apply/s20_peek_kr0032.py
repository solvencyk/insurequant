#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 20 (read-only): census row of NH농협손보 KR0032 2023.1Q (master vintage / cause / closure) -> stdout"""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
D = Path(__file__).resolve().parent.parent.parent / "d_census"
with open(D / "d_census_addl.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        if r["code"] == "KR0032" and r["quarter"] == "2023.1Q":
            for k in ("scope", "pl_items_differ", "cause_class", "cause_detail", "master_vintage", "latest_vector_closes_block", "closure_basis", "fy_block_quarters(E=equal D=differs)", "seam_neighbours_stale", "gold_cells", "disposition", "disposition_reason"):
                print(f"{k}: {r[k]}")
