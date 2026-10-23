# -*- coding: utf-8 -*-
"""Touched (code, quarter) sets per load commit + working tree, for PL_breakdown.json and CSM_waterfall.json (cell-level diff of 값)."""
import json, subprocess, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
def show(rev, path):
    b = subprocess.run(["git", "-C", ROOT, "show", f"{rev}:{path}"], capture_output=True).stdout
    return json.loads(b.decode("utf-8"))
def load_wt(path):
    return json.load(open(f"{ROOT}/{path}", encoding="utf-8"))
def idx(rows):
    return {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): (r.get("값"), r.get("값_당분기")) for r in rows}
loads = [("acdb2fe9", "acdb2fe9^", "acdb2fe9"), ("5419a817", "5419a817^", "5419a817"), ("afea4342", "afea4342^", "afea4342"),
         ("b1187788", "b1187788^", "b1187788"), ("worktree", "HEAD", None)]
out = {}
for fn in ("PL_breakdown.json", "CSM_waterfall.json"):
    for name, a, b in loads:
        A = idx(show(a, fn)); B = idx(show(b, fn) if b else load_wt(fn))
        ch = {k for k in set(A) | set(B) if A.get(k) != B.get(k)}
        cq = collections.defaultdict(list)
        for k in ch: cq[(k[0], k[2])].append(k[1])
        out[f"{fn}|{name}"] = {f"{c}|{q}": sorted(v, key=lambda x: (len(x), x)) for (c, q), v in sorted(cq.items())}
        print(fn, name, "cells", len(ch), "company-quarters", len(cq), "companies", sorted({c for c, _ in cq}))
json.dump(out, open("s01_touched.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
