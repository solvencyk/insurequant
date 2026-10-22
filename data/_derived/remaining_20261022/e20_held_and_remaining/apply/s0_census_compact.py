#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 0b: compact one-line-per-bucket view of both census csv files -> s0_census_compact.txt"""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
D = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census")
OUT = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/apply/s0_census_compact.txt")
lines = []
for fn in ("d_census_table.csv", "d_census_addl.csv"):
    with open(D / fn, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    lines.append(f"===== {fn}: {len(rows)} rows")
    for r in rows:
        fyq = r.get("fy_block_quarters(E=equal D=differs)", "")
        lines.append(
            f"{r['scope']:5s} {r['code']} {r['company'][:8]:8s} {r['quarter']} sheets={r['sheets'][:30]:30s} cls={r['cause_class'][:22]:22s} "
            f"closes={r['latest_vector_closes_block']:10s} disp={r['disposition']:14s} gold={r['gold_cells'][:60]} | pl_items={r['pl_items_differ'][:50]} csm_items={r['csm_items_differ'][:30]} | fy={fyq[:80]}"
        )
text = "\n".join(lines)
OUT.write_text(text + "\n", encoding="utf-8", newline="\n")
print(len(text))
