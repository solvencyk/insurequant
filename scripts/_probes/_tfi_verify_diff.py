# -*- coding: utf-8 -*-
"""Cell-level diff between two kics_disclosure.json snapshots -- confirms
fill_tfi_table_to_disclosure.py's write touched ONLY what it claims to:
new (code,quarter,item47-54) combos + 값_적용후 additions on existing
47-54 rows, zero changes anywhere else."""
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

before_path, after_path = sys.argv[1], sys.argv[2]
before = json.loads(Path(before_path).read_text(encoding="utf-8"))
after = json.loads(Path(after_path).read_text(encoding="utf-8"))

def index(rows):
    d = {}
    for r in rows:
        key = (r["원보험사코드"], r["공시분기"], r["항목번호"])
        d[key] = r
    return d

bi, ai = index(before), index(after)
b_keys, a_keys = set(bi), set(ai)

added = a_keys - b_keys
removed = b_keys - a_keys
common = a_keys & b_keys

print(f"before: rows={len(before)} combos={len(b_keys)}")
print(f"after:  rows={len(after)} combos={len(a_keys)}")
print(f"added combos: {len(added)}")
print(f"removed combos: {len(removed)}  (should be 0)")
if removed:
    for k in sorted(removed):
        print("  REMOVED:", k)

out_of_scope_added = [k for k in added if not (47 <= k[2] <= 54)]
print(f"added combos OUTSIDE item47-54: {len(out_of_scope_added)}  (should be 0)")
for k in sorted(out_of_scope_added)[:20]:
    print("  OUT-OF-SCOPE ADD:", k)

changed_existing = []
for k in common:
    b, a = bi[k], ai[k]
    if b.get("값") != a.get("값"):
        changed_existing.append((k, "값", b.get("값"), a.get("값")))
    if b.get("값_적용후") != a.get("값_적용후"):
        changed_existing.append((k, "값_적용후", b.get("값_적용후"), a.get("값_적용후")))

print(f"existing-row field changes: {len(changed_existing)}")
out_of_scope_changes = [c for c in changed_existing if not (47 <= c[0][2] <= 54)]
in_scope_changes = [c for c in changed_existing if 47 <= c[0][2] <= 54]
print(f"  outside item47-54 (should be 0): {len(out_of_scope_changes)}")
for c in out_of_scope_changes[:20]:
    print("    OUT-OF-SCOPE CHANGE:", c)
print(f"  within item47-54 (post-fills, expected): {len(in_scope_changes)}")
values_changed = [c for c in in_scope_changes if c[1] == "값"]
print(f"    of which '값' (pre) itself changed (should be 0 -- never touched): {len(values_changed)}")
for c in values_changed:
    print("      VALUE_CHANGED (should not happen):", c)
