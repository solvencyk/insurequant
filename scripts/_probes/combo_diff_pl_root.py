import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

before = json.loads(open(sys.argv[1], encoding="utf-8").read())
after = json.loads(open("PL_breakdown.json", encoding="utf-8").read())


def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


b = {key(r): r for r in before}
a = {key(r): r for r in after}

added = [k for k in a if k not in b]
removed = [k for k in b if k not in a]
changed = [k for k in a if k in b and a[k] != b[k]]

print(f"before: {len(before)} rows, after: {len(after)} rows")
print(f"added: {len(added)}  removed: {len(removed)}  changed: {len(changed)}")
non32_added = [k for k in added if k[1] != 32]
print(f"added rows with item != 32 (SHOULD BE 0): {len(non32_added)}")
for k in non32_added[:10]:
    print("  UNEXPECTED added:", k)
print(f"added rows with item == 32: {sum(1 for k in added if k[1] == 32)}")

# for changed rows, show WHICH field differs and whether it's just 값_당분기 (expected: some
# item32 quarters ripple into neighboring quarters' 값_당분기 via YTD-diff, same as items 25-31
# did originally) vs something on items 1-31 (would be a red flag)
by_item = {}
for k in changed:
    by_item.setdefault(k[1], []).append(k)
print("changed rows grouped by item number:")
for item, ks in sorted(by_item.items(), key=lambda x: str(x[0])):
    print(f"  item {item}: {len(ks)} rows")
    for k in ks[:3]:
        diffs = {f: (b[k].get(f), a[k].get(f)) for f in a[k] if a[k].get(f) != b[k].get(f)}
        print("     ", k, diffs)
