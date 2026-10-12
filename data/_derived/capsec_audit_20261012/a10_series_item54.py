# -*- coding: utf-8 -*-
"""a10: quarterly series of items 3 / 47 / 48 / 49 / 53 / 54 for companies given on the command line (read-only)."""
import json
import sys
from collections import defaultdict

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
d = json.load(open(ROOT + "/kics_disclosure.json", encoding="utf-8"))
QS = ["%d.%dQ" % (y, n) for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)][:14]
want = set(sys.argv[1:])
S = defaultdict(dict)
nm = {}
for r in d:
    if r["원보험사코드"] in want and r["항목번호"] in (3, 6, 47, 48, 49, 53, 54):
        S[(r["원보험사코드"], r["항목번호"], "pre")][r["공시분기"]] = r.get("값")
        S[(r["원보험사코드"], r["항목번호"], "post")][r["공시분기"]] = r.get("값_적용후")
        nm[r["원보험사코드"]] = r["원수사명"]


def f(x):
    try:
        return "%.1f" % float(str(x).replace(",", ""))
    except Exception:
        return "." if x in (None, "", "-") else str(x)


for code in sorted(want):
    print("==", code, nm.get(code))
    print("  qtr      i3pre    i3post    i47pre   i47post     i48pre      i49     i53     i54pre   i54post   i6")
    for q in QS:
        g = lambda it, c="pre": S.get((code, it, c), {}).get(q)
        print("  %s %9s %9s %9s %9s %10s %8s %7s %9s %9s %7s" % (
            q, f(g(3)), f(g(3, "post")), f(g(47)), f(g(47, "post")), f(g(48)), f(g(49)), f(g(53)), f(g(54)), f(g(54, "post")), f(g(6))))
