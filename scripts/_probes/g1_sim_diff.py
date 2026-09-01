# -*- coding: utf-8 -*-
import json, io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
old = json.loads((REPO / "scripts/_probes/_g1_sim_old.json").read_text(encoding="utf-8"))
new = json.loads((REPO / "scripts/_probes/_g1_sim_new2.json").read_text(encoding="utf-8"))

new_keys = sorted(set(new) - set(old))
lost_keys = sorted(set(old) - set(new))
changed = sorted(k for k in (set(old) & set(new)) if old[k] != new[k])

print(f"new_keys (None->value) : {len(new_keys)}")
print(f"lost_keys (value->None): {len(lost_keys)}")
print(f"changed_keys (value->different value): {len(changed)}")

by_item = {}
for k in new_keys:
    code, tq, it = k.split("|")
    by_item.setdefault(int(it), []).append((code, tq, new[k]))

print("\n--- new_keys by item number ---")
for it in sorted(by_item):
    entries = by_item[it]
    vals = sorted(set(v for _, _, v in entries))
    print(f"  item{it}: {len(entries)} cells, distinct values={vals[:10]}{'...' if len(vals)>10 else ''}")

print("\n--- full list of new_keys for items NOT in {24,25,26} (should be empty or explained) ---")
off_target = [k for k in new_keys if not k.split("|")[2] in ("24", "25", "26")]
for k in off_target:
    print(f"  {k} -> {new[k]!r}")

print(f"\n--- changed_keys detail (old -> new) ---")
for k in changed:
    print(f"  {k}: {old[k]!r} -> {new[k]!r}")

print("\n--- new_keys for item 24/25/26 (full list) ---")
for it in (24, 25, 26):
    for code, tq, v in sorted(by_item.get(it, [])):
        print(f"  item{it} {code} {tq} -> {v!r}")
