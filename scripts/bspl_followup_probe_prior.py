#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per filing of a fiscal year: the value of one concept in every column (cur / prior-year-end / ...) of every bs_full table (read-only).
   usage: bspl_followup_probe_prior.py KR0068 "10:현금및현금성자산" 2023   [group K|S]"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from bspl_granularity import stage_b as B  # noqa: E402

code, name, fy = sys.argv[1], sys.argv[2], int(sys.argv[3])
all_v, anchor, disc, meta = B.load_master()
for q in [f"{fy}.{n}Q" for n in (1, 2, 3, 4)] + [f"{fy + 1}.{n}Q" for n in (1, 2)]:
    doc = B.load_tables(code, q)
    if doc is None:
        print(q, "no tables")
        continue
    obs, ui, notes = B.observations(code, q, doc, all_v, disc, None)
    for o in obs:
        if B.cname(o.concept) == name and o.kind in ("bs_full", "sum_bs", "equity"):
            print(f"{q} {o.kind:<7} form={o.form} p{o.page} col{o.col} period={o.quarter} value_mn={o.value_mn:,.3f} unit={o.unit}")
