# -*- coding: utf-8 -*-
import json
from pathlib import Path
d = Path(r"C:/Users/sangwook.cho/Desktop/insurequant/artifacts/kics_validation")
base = json.loads((d/"report_20260831T202215Z.json").read_text(encoding="utf-8"))  # live snapshot
sim  = json.loads((d/"report_20260831T202155Z.json").read_text(encoding="utf-8"))  # SIM2
def rs(rep): return {(f.get("rule"), f.get("원보험사코드"), f.get("공시분기")): f for f in rep["findings"] if f.get("status")=="RED"}
b,s = rs(base), rs(sim)
print(f"live RED={len(b)}  SIM2 RED={len(s)}")
print("\n== 닫힌 ==")
for k in sorted(set(b)-set(s)): print("   -", k, b[k].get("diff"))
print("\n== 새로 생긴 ==")
for k in sorted(set(s)-set(b)): print("   +", k, s[k].get("diff"), "|", str(s[k].get("detail"))[:120])
print("\n== SIM2 에 남은 RED 전건 ==")
import collections
c=collections.Counter()
for k in sorted(s):
    c[k[1]]+=1
for k in sorted(s):
    print(f"   {k[0]:28s} {k[1]} {k[2]}")
print("\n   회사별:", dict(c))
