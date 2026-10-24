# -*- coding: utf-8 -*-
"""CSM_waterfall.json + PL_breakdown.json: leaf diff HEAD~1 vs HEAD, grouped by company/item (read-only)."""
import json
import subprocess
from collections import Counter, defaultdict

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"


def show(ref, path):
    return json.loads(subprocess.check_output(["git", "-C", ROOT, "show", f"{ref}:{path}"]).decode("utf-8"))


for path in ["CSM_waterfall.json", "PL_breakdown.json"]:
    old, new = show("d5077c7b", path), show("HEAD", path)
    k = lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"])
    ko = {k(r): r for r in old}
    kn = {k(r): r for r in new}
    print(path, "rows", len(old), len(new), "keys equal", set(ko) == set(kn))
    per_co = Counter()
    per_item = defaultdict(Counter)
    qs = defaultdict(set)
    for key in kn:
        a, b = ko.get(key, {}), kn[key]
        for f in set(a) | set(b):
            if a.get(f) != b.get(f):
                per_co[key[0]] += 1
                per_item[key[0]][key[2]] += 1
                qs[key[0]].add(key[1])
    print("  cells", sum(per_co.values()), dict(per_co))
    for c in sorted(per_co):
        print("  ", c, "quarters", sorted(qs[c]), "items", dict(sorted(per_item[c].items())))
