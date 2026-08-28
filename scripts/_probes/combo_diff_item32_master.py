"""Combo-diff pl_breakdown_master.json before/after the item32 patch: confirm items 1-31
(and the 코리안리 string-keyed extra items) are byte-identical, and the ONLY change is new
item32 rows."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

before = json.loads(open(sys.argv[1], encoding="utf-8").read())
after = json.loads(open("data/dart/viz/pl_breakdown_master.json", encoding="utf-8").read())


def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


b = {key(r): r for r in before}
a = {key(r): r for r in after}

added = [k for k in a if k not in b]
removed = [k for k in b if k not in a]
changed = [k for k in a if k in b and a[k] != b[k]]

print(f"before: {len(before)} rows, after: {len(after)} rows")
print(f"added: {len(added)}  removed: {len(removed)}  changed(non-key fields): {len(changed)}")
non32_added = [k for k in added if k[1] != 32]
print(f"added rows with item != 32 (SHOULD BE 0): {len(non32_added)}")
for k in non32_added[:10]:
    print("  UNEXPECTED:", k)
print(f"added rows with item == 32: {sum(1 for k in added if k[1] == 32)}")
if changed:
    print("CHANGED rows (should be empty):")
    for k in changed[:10]:
        print("  ", k, "before=", b[k], "after=", a[k])
