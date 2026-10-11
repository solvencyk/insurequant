import json, sys
sys.stdout.reconfigure(encoding="utf-8")
D = "data/_derived/bspl_apply_20261011/item16/"
def load(p):
    rows = json.load(open(p, encoding="utf-8"))
    return {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}
new = load("PL_breakdown.json")
for label, p in (("pre-apply backup", "data/_derived/bspl_apply_backup_20261011/item16/PL_breakdown.json"), ("HEAD", D + "_head_PL.json")):
    old = load(p)
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = [k for k in old if k in new and old[k] != new[k]]
    print(f"== vs {label}: rows {len(old)} -> {len(new)}; added {len(added)}; removed {len(removed)}; changed {len(changed)}")
    item16_added = [k for k in added if k[1] == "16"]
    print("   added item16:", len(item16_added), "other added:", [k for k in added if k[1] != "16"][:5])
    if label.startswith("pre"):
        for k in changed:
            o, n = old[k], new[k]
            print("   changed", k, {f: (o.get(f), n.get(f)) for f in set(o) | set(n) if o.get(f) != n.get(f)})
    else:
        from collections import Counter
        c = Counter()
        for k in changed:
            o, n = old[k], new[k]
            c[tuple(sorted(f for f in set(o) | set(n) if o.get(f) != n.get(f)))] += 1
        print("   changed field-sets:", dict(c))
        mine = {("KR1101", "16", "2024.2Q"), ("KR1103", "16", "2024.2Q")}
        print("   changed rows with item 16 of KR1101/KR1103:", [k for k in changed if k[1] == "16" and k[0] in ("KR1101", "KR1103")])
