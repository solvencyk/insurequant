# -*- coding: utf-8 -*-
"""c2c: sanity identity of the K-ICS capital build-up for the companies on the command line, per quarter (값 column):
   item2 (기본자본) == item4 (순자산) - item12 (불인정) - item13 (보완자본으로 재분류)      [Ⅲ.2.나.(2)]
   item1 == item2 + item3
   item3 == item13 + (부채자본증권 등) -> shown as item3 - item13 (the 후순위 + other 보완자본 not coming from the 재분류)
Read-only. Used to be sure the X = item13 - item49 series is a clean measurement.
"""
import json
import sys
from collections import defaultdict

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
QS = ["%d.%dQ" % (y, n) for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)][:14]
kd = json.load(open(ROOT + "/kics_disclosure.json", encoding="utf-8"))
want = set(sys.argv[1:])
S = defaultdict(dict)
for r in kd:
    if r["원보험사코드"] in want and r["항목번호"] in (1, 2, 3, 4, 12, 13, 49):
        try:
            S[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = float(str(r.get("값")).replace(",", ""))
        except Exception:
            pass
for code in sorted(want):
    print("==", code)
    print("  qtr      i1       i2       i3       i4      i12      i13      i49   | i2-(i4-i12-i13)  i1-(i2+i3)  i3-i13")
    for q in QS:
        v = {k: S.get((code, k), {}).get(q) for k in (1, 2, 3, 4, 12, 13, 49)}
        def f(x):
            return "." if x is None else "%.1f" % x
        a = None if None in (v[2], v[4], v[12], v[13]) else v[2] - (v[4] - v[12] - v[13])
        b = None if None in (v[1], v[2], v[3]) else v[1] - (v[2] + v[3])
        c = None if None in (v[3], v[13]) else v[3] - v[13]
        print("  %s %8s %8s %8s %8s %8s %8s %8s | %12s %12s %9s" % (q, f(v[1]), f(v[2]), f(v[3]), f(v[4]), f(v[12]), f(v[13]), f(v[49]), f(a), f(b), f(c)))
