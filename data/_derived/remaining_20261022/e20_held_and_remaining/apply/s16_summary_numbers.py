#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 16: numbers for the ticket answer / TODO / changelog (read-only) -> s16_summary_numbers.txt"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / "e20_plan.json").read_text(encoding="utf-8"))
L = []
tot_cells = 0
ro_total = 0
by_co = defaultdict(lambda: dict(buckets=[], cells=0, replaced=0, rounding_only=0))
maxdiff = 0.0
n_fs = 0
for b in plan["buckets"]:
    if "error" in b:
        continue
    d = by_co[b["code"]]
    d["buckets"].append(f"{b['quarter']}({','.join(str(i) for i in b['adopt_items'])})")
    d["cells"] += len(b["cells"])
    d["replaced"] += sum(1 for c in b["cells"] if c["gold_cell"])
    d["rounding_only"] += len(b["rounding_only_items"])
    tot_cells += len(b["cells"])
    ro_total += len(b["rounding_only_items"])
    for c in b["cells"]:
        if c["fsapi_diff"] is not None:
            n_fs += 1
            maxdiff = max(maxdiff, abs(c["fsapi_diff"]))
for code, d in sorted(by_co.items()):
    L.append(f"{code}: buckets {d['buckets']} cells {d['cells']} replaced-gold {d['replaced']} rounding_only_items(not touched) {d['rounding_only']}")
L.append(f"TOTAL cells {tot_cells}; rounding-only items left untouched across buckets: {ro_total}; FS-API second source: {n_fs} cells, max |diff| {maxdiff}")
c = plan["apply_contract"]
L.append(f"contract: gold_new {len(c['gold_new'])}, gold_replace {len(c['gold_replace'])}, null_dangi_add {len(c['null_dangi_add'])}, set_dangi_add {len(c['set_dangi_add'])}, set_dangi_remove {len(c['set_dangi_remove'])}, held {len(c['held'])}")
L.append("replaced gold cells (old gold value = original-vintage print -> latest comparative):")
for e in c["gold_replace"]:
    lines = e["note"]
    L.append(f"  {e['code']} {e['quarter']} i{e['item']}: {e['was']} -> {e['value']}  (was in old entry: {e['old_entry'].get('was')})")
L.append("null_dangi by company/quarter: " + json.dumps(dict(Counter(f"{x[0]} {x[1]}" for x in c["null_dangi_add"])), ensure_ascii=False))
(HERE / "s16_summary_numbers.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
print("\n".join(L))
