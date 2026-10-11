# -*- coding: utf-8 -*-
"""a09 (read-only): key-level diff of data/dart/viz/csm_amort_schedule.json against the pre-fix backup.

Proves (1) same top-level keys, same company list in the same order, (2) which company entries changed and WHICH FIELDS of each,
(3) every other entry (incl. the 7 reinsurers appended from the master) is identical.
Usage: a09_panel_diff.py [new_path] [old_path]"""
from __future__ import annotations

import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
sys.stdout.reconfigure(encoding="utf-8")

new_p = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/dart/viz/csm_amort_schedule.json"
old_p = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data/_derived/amort_fix_backup_20261011/csm_amort_schedule.json.pre_fix"
new = json.loads(new_p.read_text(encoding="utf-8"))
old = json.loads(old_p.read_text(encoding="utf-8"))
print("top-level keys equal:", new.keys() == old.keys(), "| period:", old.get("period"), "->", new.get("period"))
on, nn = [c["company"] for c in old["companies"]], [c["company"] for c in new["companies"]]
print("company list + order identical:", on == nn, f"({len(on)} -> {len(nn)})")
changed = []
for o, n in zip(old["companies"], new["companies"]):
    if o == n:
        continue
    fields = sorted(k for k in set(o) | set(n) if o.get(k) != n.get(k))
    changed.append((o["company"], fields, o, n))
print(f"entries changed: {len(changed)} | identical: {len(old['companies']) - len(changed)}")
for co, fields, o, n in changed:
    yo, yn = o.get("yearly") or {}, n.get("yearly") or {}
    print(f"  {co:<14s} fields={fields}  y1 {yo.get('y1')} -> {yn.get('y1')}  y5 {yo.get('y5')} -> {yn.get('y5')}  total {(o.get('buckets') or {}).get('total')} -> {(n.get('buckets') or {}).get('total')}  status {o.get('status')}->{n.get('status')}")
unchanged_fields = {"rcept_no", "status", "unit", "unit_detected", "unit_source", "period", "as_of"}
odd = [(co, [f for f in fields if f in unchanged_fields]) for co, fields, o, n in changed if any(f in unchanged_fields for f in fields)]
print("changed entries whose rcept/status/unit/period/as_of moved (expected none):", odd)
json.dump({"changed": [c[0] for c in changed], "fields": {c[0]: c[1] for c in changed}}, (W / "a09_panel_diff.json").open("w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
