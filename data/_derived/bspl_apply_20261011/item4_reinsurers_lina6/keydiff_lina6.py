import json, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
D = "data/_derived/bspl_apply_20261011/item4_reinsurers_lina6/"
B = "data/_derived/bspl_apply_backup_20261011/item4_reinsurers_lina6/"
QS = {"2023.3Q", "2024.1Q", "2024.2Q", "2024.3Q", "2025.1Q", "2025.2Q"}


def load(p):
    rows = json.load(open(p, encoding="utf-8"))
    return {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}


new = load("PL_breakdown.json")
ok = True
for label, p in (("pre-apply backup", B + "PL_breakdown.json"), ("HEAD (git show HEAD:PL_breakdown.json)", D + "_head_PL.json")):
    old = load(p)
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = [k for k in old if k in new and old[k] != new[k]]
    item4_lina = [k for k in added if k[0] == "KR0074" and k[1] == "4"]
    other_added = [k for k in added if k not in item4_lina]
    print(f"== PL rows vs {label}: {len(old)} -> {len(new)}; added {len(added)} (KR0074 item 4: {len(item4_lina)} = {[k[2] for k in item4_lina]}; other: {len(other_added)}); removed {len(removed)}; changed {len(changed)}")
    k74_old = {k: v for k, v in old.items() if k[0] == "KR0074"}
    k74_diff = [k for k, v in k74_old.items() if new.get(k) != v]
    print(f"   KR0074 pre-existing rows {len(k74_old)}: changed/removed {len(k74_diff)}")
    held = [k for k in new if k[0] == "KR0074" and k[1] == "4" and k[2] in ("2023.1Q", "2023.2Q")]
    print("   held 2023.1Q/2Q item 4 present:", held)
    if other_added or removed or changed or k74_diff or held or {k[2] for k in item4_lina} != QS or len(item4_lina) != 6:
        ok = False
        print("   !! other_added", other_added[:5], "removed", removed[:5], "changed", changed[:5])
    for k in item4_lina:
        r = new[k]
        assert r["항목명"] == "원수 CSM상각" and r["값"] > 0 and isinstance(r["항목번호"], int), r
    print("   new rows:", [(k[2], new[k]["값"], new[k]["값_당분기"]) for k in item4_lina])


def loads(p):
    d = json.load(open(p, encoding="utf-8"))
    return d, {(c["company_code"], c["quarter"], c["item_block"]): c for c in d["cells"]}


for label, p in (("pre-apply backup", B + "PL_breakdown_provenance.json"), ("HEAD", D + "_head_PL_provenance.json")):
    od, oc = loads(p)
    nd, nc = loads("PL_breakdown_provenance.json")
    added = sorted(set(nc) - set(oc))
    removed = sorted(set(oc) - set(nc))
    changed = [k for k in oc if k in nc and oc[k] != nc[k]]
    top_changed = [k for k in od if k != "cells" and od[k] != nd.get(k)]
    top_added = [k for k in nd if k != "cells" and k not in od]
    print(f"== sidecar vs {label}: cells {len(oc)} -> {len(nc)}; added {len(added)} ({dict(Counter(k[2] for k in added))}); removed {len(removed)}; changed {len(changed)}; top-level added {top_added}; top-level changed {top_changed}")
    if removed or changed or top_changed or len(added) != 6 or any(k[2] != "contract_notes" or k[0] != "KR0074" for k in added):
        ok = False
print("KEYDIFF", "OK: only 6 KR0074 item-4 rows + 6 contract_notes sidecar blocks were added; every pre-existing row/block identical" if ok else "FAILED")
