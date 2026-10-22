# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); OUT = ROOT / "data/_derived/remaining_20261022/d_census"
res = json.loads((OUT / "d1_scan.json").read_text(encoding="utf-8"))
def differs(a, b, floor, rel=0.001): return a is not None and b is not None and abs(a - b) > max(rel * abs(a), floor)
setA = {}
for r in res:
    d = {k: v for k, v in r["items"].items() if k in ("1", "22", "23", "24") and differs(v["same"], v["prior"], 200)}
    if d: setA[(r["code"], r["q"])] = r
print("setA (items 1/22/23/24, floor 200mn):", len(setA), "buckets;", len({c for c, _ in setA}), "companies")
# compare with stored list
old = [l.split(" diffs")[0] for l in (ROOT / "data/_derived/kyobo_validation_20261022/sim_other_vintage_buckets.txt").read_text(encoding="utf-8").splitlines()]
names = {r["name"]: r["code"] for r in res}
oldset = set()
for l in old:
    nm, q = l.rsplit(" ", 1); oldset.add((names.get(nm), q))
print("stored list:", len(oldset), "only-in-new:", sorted(set(setA) - oldset), "only-in-old:", sorted(oldset - set(setA)))
# wider
setB = {}
for r in res:
    d = {k: v for k, v in r["items"].items() if differs(v["same"], v["prior"], 1.0)}
    if d: setB[(r["code"], r["q"])] = (r, d)
print("setB (any item, floor 1mn):", len(setB), "buckets;", len({c for c, _ in setB}), "companies")
extra = sorted(set(setB) - set(setA))
cnt = defaultdict(list)
for k in extra:
    r, d = setB[k]; cnt[(r["code"], r["name"])].append((k[1], sorted(d, key=lambda x: (len(x), x))))
for (c, n), L in sorted(cnt.items()):
    print(c, n, L)
print("div mismatch (same vs prior):", [(r['code'], r['q'], r['div_same'], r['div_prior']) for r in res if r['div_same'] != r['div_prior']])
