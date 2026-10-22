#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 19 (read-only): how do the 21 loaded buckets split over the two census files, and what is left? -> s19_scope_check.txt"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
D = HERE.parent.parent / "d_census"
L = []


def rows(name):
    with open(D / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


addl, tab = rows("d_census_addl.csv"), rows("d_census_table.csv")
plan = json.loads((HERE / "e20_plan.json").read_text(encoding="utf-8"))
loaded = {(b["code"], b["quarter"]) for b in plan["buckets"]}
L.append(f"loaded buckets {len(loaded)}; d_census_addl rows {len(addl)}; d_census_table rows {len(tab)}")
L.append("scope counts addl: " + str(dict(Counter(r["scope"] for r in addl))))
L.append("scope counts table: " + str(dict(Counter(r["scope"] for r in tab))))
L.append("closes(YES/NO) by scope addl: " + str(dict(Counter((r["scope"], r["latest_vector_closes_block"]) for r in addl))))
L.append("closes(YES/NO) by scope table: " + str(dict(Counter((r["scope"], r["latest_vector_closes_block"]) for r in tab))))
L.append("disposition table: " + str(dict(Counter((r["scope"], r["disposition"]) for r in tab))))
L.append("disposition addl: " + str(dict(Counter((r["scope"], r["disposition"]) for r in addl))))
inaddl = {(r["code"], r["quarter"]): r for r in addl}
intab = {(r["code"], r["quarter"]): r for r in tab}
L.append("per loaded bucket: where it sits in the census")
for k in sorted(loaded):
    a, t = inaddl.get(k), intab.get(k)
    L.append(f"  {k}: addl={None if not a else (a['scope'], a['latest_vector_closes_block'], a['disposition'])} table={None if not t else (t['scope'], t['latest_vector_closes_block'], t['disposition'])}")
only_addl = [k for k in loaded if k in inaddl and k not in intab]
only_tab = [k for k in loaded if k in intab and k not in inaddl]
both = [k for k in loaded if k in intab and k in inaddl]
neither = [k for k in loaded if k not in intab and k not in inaddl]
L.append(f"loaded in addl only {len(only_addl)}; table only {len(only_tab)}; both {len(both)}; neither {len(neither)} {sorted(neither)}")
L.append("")
L.append("still not loaded after this round:")
rest_addl = [r for r in addl if (r["code"], r["quarter"]) not in loaded]
rest_tab = [r for r in tab if (r["code"], r["quarter"]) not in loaded]
L.append(f"  addl not loaded {len(rest_addl)}: " + str(dict(Counter((r["scope"], r["latest_vector_closes_block"], r["disposition"]) for r in rest_addl))))
L.append(f"  table not loaded {len(rest_tab)}: " + str(dict(Counter((r["scope"], r["latest_vector_closes_block"], r["disposition"]) for r in rest_tab))))
L.append("  table (STAY/OWNER_DECISION) rows that were adopted already in round 18 are not in this file; see TODO Status 18차")
(HERE / "s19_scope_check.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
print("\n".join(L))
