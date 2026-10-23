# -*- coding: utf-8 -*-
"""Validation stage: derive changed cells of PL_breakdown.json (WT vs HEAD). Read-only."""
import json, subprocess, sys, os
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val"

def head(path):
    b = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + path], capture_output=True).stdout
    return json.loads(b.decode("utf-8"))

def wt(path):
    with open(ROOT + "/" + path, encoding="utf-8") as f:
        return json.load(f)

def idx(rows):
    d = {}
    dup = 0
    for r in rows:
        k = (r["원보험사코드"], r["공시분기"], r["항목번호"])
        if k in d:
            dup += 1
        d[k] = r
    return d, dup

res = {}
lines = []
for fn in ["PL_breakdown.json", "CSM_waterfall.json"]:
    h = head(fn); w = wt(fn)
    hi, hd = idx(h); wi, wd = idx(w)
    lines.append(f"{fn}: HEAD rows {len(h)} dup {hd}; WT rows {len(w)} dup {wd}")
    added = [k for k in wi if k not in hi]
    removed = [k for k in hi if k not in wi]
    lines.append(f"  added keys {len(added)}, removed keys {len(removed)}")
    ch = []
    otherfield = []
    for k in wi:
        if k in hi:
            a, b = hi[k], wi[k]
            for fld in set(a) | set(b):
                if a.get(fld) != b.get(fld):
                    if fld in ("값", "값_당분기"):
                        ch.append((k, fld, a.get(fld), b.get(fld)))
                    else:
                        otherfield.append((k, fld, a.get(fld), b.get(fld)))
    lines.append(f"  changed value-field cells {len(ch)}; other-field changes {len(otherfield)}")
    for k, fld, a, b in sorted(ch, key=lambda x: (x[0][0], x[0][1], x[0][2], x[1])):
        lines.append(f"    {k[0]} {k[1]} item{k[2]} {fld}: {a} -> {b}")
    for o in otherfield[:20]:
        lines.append(f"    OTHER {o}")
    res[fn] = [(list(k), fld, a, b) for k, fld, a, b in ch]
with open(OUT + "/a01_diff.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
with open(OUT + "/a01_diff.json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False)
print("\n".join(lines[:3]))
