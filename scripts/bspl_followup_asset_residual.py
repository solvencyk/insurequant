#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Asset-side and liability-side sanity for every (company, quarter) bucket that received an added/changed BS cell vs git HEAD (read-only).
   asset residual   = 자산총계 - (10+11+12+13+14+15)   (other assets: must be >= 0 when all six lines exist)
   liability resid. = 부채총계 - (20+21+22+23+24)       (other liabilities: must be >= 0 when all five lines exist)
   equity resid.    = 자본총계 - (30+31+4)              (자본잉여금 + 자본조정 ...: printed, no sign rule)"""
import json, subprocess, sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
head = json.loads(subprocess.run(["git", "show", "HEAD:IFRS17_BS.json"], cwd=ROOT, capture_output=True).stdout.decode("utf-8"))
cur = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
hk = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in head}
ck = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in cur}
touched = defaultdict(set)
for k, v in ck.items():
    if k not in hk or hk[k] != v:
        touched[(k[0], k[2])].add(k[1])
mv = defaultdict(dict)
for (c, it, q), v in ck.items():
    if v is not None:
        mv[(c, q)][it] = v
bad = 0
rows = []
for (c, q), items in sorted(touched.items()):
    m = mv[(c, q)]
    a = m.get(1)
    out = []
    if a is not None and all(i in m for i in (10, 11, 12, 13, 14, 15)):
        r = a - sum(m[i] for i in (10, 11, 12, 13, 14, 15))
        out.append(f"asset-other {r/100:,.1f}억 ({100*r/a:.1f}%)")
        if r < -1.0:
            bad += 1; out.append("NEGATIVE")
    l = m.get(2)
    if l is not None and all(i in m for i in (20, 21, 22, 23, 24)):
        r = l - sum(m[i] for i in (20, 21, 22, 23, 24))
        out.append(f"liab-other {r/100:,.1f}억 ({100*r/l:.1f}%)")
        if r < -1.0:
            bad += 1; out.append("NEGATIVE")
    e = m.get(3)
    if e is not None and all(i in m for i in (30, 31, 4)):
        r = e - sum(m[i] for i in (30, 31, 4))
        out.append(f"equity-other {r/100:,.1f}억")
    if out:
        rows.append(f"{c} {q} touched items {sorted(items)}: " + " | ".join(out))
print(len(touched), "touched buckets;", len(rows), "with a testable identity;", bad, "negative residuals")
print("\n".join(rows))
