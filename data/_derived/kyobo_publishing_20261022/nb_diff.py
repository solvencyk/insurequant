# -*- coding: utf-8 -*-
import json, subprocess, sys
new = json.load(open("NB_CSM_multiple.json", encoding="utf-8"))
old = json.loads(subprocess.check_output(["git", "show", "HEAD:NB_CSM_multiple.json"]).decode("utf-8"))
print("rows", len(old), "->", len(new))
ko = {(r["원보험사코드"], r["공시분기"]): r for r in old}
kn = {(r["원보험사코드"], r["공시분기"]): r for r in new}
print("keys equal", set(ko) == set(kn))
ncell = 0
for k in sorted(kn):
    a, b = ko.get(k, {}), kn[k]
    d = {f: (a.get(f), b.get(f)) for f in set(a) | set(b) if a.get(f) != b.get(f)}
    if d:
        ncell += len(d)
        print(k, d)
print("changed cells", ncell)
