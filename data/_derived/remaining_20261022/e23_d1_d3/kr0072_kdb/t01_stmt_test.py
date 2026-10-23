# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from kdb_stmt import Stmt, items_from, identities, LABELS
D = "data/dart"
N = {"N1": f"{D}/FY2024_Q1/raw/KR0072_케이디비생명보험/20240516000597.xml", "N2": f"{D}/FY2024_Q2/raw/KR0072_케이디비생명보험/20240814000801.xml",
     "N3": f"{D}/FY2024_Q3/raw/KR0072_케이디비생명보험/20241114000809.xml", "N4": f"{D}/FY2024_Q4/raw/KR0072_케이디비생명보험_20250331002302/20250331002302.xml"}
for k, rel in N.items():
    S = Stmt(rel)
    print("=====", k, "unit", S.unit, "periods", {o: p["end"] for o, p in S.periods.items()}, "paths", S.paths)
    V = S.read(2023, "cum")
    it = items_from(V)
    print("  col", V["ins_result"]["col"], V["ins_result"]["header"], "line of 보험손익", V["ins_result"]["line"], V["ins_result"]["printed"])
    print("  items", {i: round(v, 6) for i, v in sorted(it.items())})
    for name, d, ok in identities(V):
        print("   ", "OK" if ok else "FAIL", f"{d:+.6f}", name)
