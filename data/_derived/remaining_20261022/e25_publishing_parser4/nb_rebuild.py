# -*- coding: utf-8 -*-
"""Rebuild NB_CSM_multiple rows into a temp file (never touches the master), diff vs committed master,
and optionally write ONLY the differing cells (guarded: current master cell must equal the HEAD value).
Usage: nb_rebuild.py --check | --apply
"""
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
E = ROOT / "data/_derived/remaining_20261022/e25_publishing_parser4"
TMP = E / "nb_rebuilt_tmp.json"

spec = importlib.util.spec_from_file_location("bnm", ROOT / "scripts/build_nb_csm_multiple.py")
bnm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bnm)
bnm.OUT = TMP
bnm.main()

master_path = ROOT / "NB_CSM_multiple.json"
raw = master_path.read_text(encoding="utf-8")
cur = json.loads(raw)
head = json.loads(subprocess.check_output(["git", "-C", str(ROOT), "show", "HEAD:NB_CSM_multiple.json"]).decode("utf-8"))
new = json.loads(TMP.read_text(encoding="utf-8"))
print("roundtrip identical to disk:", json.dumps(cur, ensure_ascii=False, indent=2) == raw)
print("disk == HEAD:", cur == head)
key = lambda r: (r["원보험사코드"], r["공시분기"])
kc = {key(r): r for r in cur}
kn = {key(r): r for r in new}
print("rows cur/new:", len(cur), len(new), "keys equal:", set(kc) == set(kn))
diffs = []
for k in sorted(kn):
    a, b = kc[k], kn[k]
    for f in sorted(set(a) | set(b)):
        if a.get(f) != b.get(f):
            diffs.append((k, f, a.get(f), b.get(f)))
print("changed cells:", len(diffs))
print("by company:", dict(Counter(d[0][0] for d in diffs)))
print("by quarter:", dict(sorted(Counter(d[0][1] for d in diffs).items())))
print("by field:", dict(Counter(d[1] for d in diffs)))
for k, f, x, y in diffs:
    print("  ", k, f, x, "->", y)

if "--apply" in sys.argv:
    n = 0
    for k, f, x, y in diffs:
        assert kc[k].get(f) == x, ("guard", k, f)
        kc[k][f] = y
        n += 1
    master_path.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    print("APPLIED cells:", n)
