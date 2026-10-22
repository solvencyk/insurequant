#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 0: read-only view of d_census_table.csv / d_census_addl.csv (key columns) -> s0_census_view.txt"""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
D = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census")
OUT = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/apply/s0_census_view.txt")
lines = []
KEYS = ["scope", "code", "company", "quarter", "sheets", "cause_class", "latest_vector_closes_block", "closure_basis", "fy_block_quarters",
        "gold_cells", "disposition", "disposition_reason"]
for fn in ("d_census_table.csv", "d_census_addl.csv"):
    with open(D / fn, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    lines.append(f"===== {fn}: {len(rows)} rows; columns: {list(rows[0].keys())}")
    for r in rows:
        parts = []
        for k in KEYS:
            v = r.get(k)
            if v is None:
                continue
            parts.append(f"{k}={v[:260]}")
        lines.append(" | ".join(parts))
text = "\n".join(lines)
OUT.write_text(text + "\n", encoding="utf-8", newline="\n")
print(text)
