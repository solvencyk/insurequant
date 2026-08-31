# -*- coding: utf-8 -*-
"""적용전/적용후 리포트 RED 집합 diff."""
import json, os, glob
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
d = ROOT/"artifacts/kics_validation"
base = json.loads((d/"report_20260831T201933Z.json").read_text(encoding="utf-8"))
sim  = json.loads((d/"report_20260831T202004Z.json").read_text(encoding="utf-8"))
def redset(rep):
    return {(f.get("rule"), f.get("원보험사코드"), f.get("공시분기")): f
            for f in rep["findings"] if f.get("status")=="RED"}
b, s = redset(base), redset(sim)
print(f"base RED={len(b)}  sim RED={len(s)}")
print("\n== 닫힌 RED (사라짐) ==")
for k in sorted(set(b)-set(s)): print("   -", k, "diff=", b[k].get("diff"))
print("\n== 새로 생긴 RED ==")
for k in sorted(set(s)-set(b)):
    print("   +", k, "diff=", s[k].get("diff"), "|", str(s[k].get("detail"))[:150])
print("\n== 남은 blocking 후보(내 5건 중) ==")
MINE = [("2_tier1_bridge","KR0080","2024.3Q"),("47_tier2_census","KR0097","2024.4Q"),
        ("47_tier2_census","KR1010","2023.2Q"),("47_tier2_census","KR1010","2023.3Q"),
        ("8_life","KR0069","2024.4Q")]
for k in MINE:
    print(f"   {k}: base={'RED' if k in b else '-'} sim={'RED' if k in s else 'CLOSED'}")
# status 변화 전수(내 5개 버킷)
print("\n== 내 5버킷의 모든 rule status 변화 ==")
BUCKETS = {("KR0080","2024.3Q"),("KR0097","2024.4Q"),("KR1010","2023.2Q"),("KR1010","2023.3Q"),("KR0069","2024.4Q")}
def allset(rep):
    o={}
    for f in rep["findings"]:
        k=(f.get("원보험사코드"), f.get("공시분기"))
        if k in BUCKETS: o[(k,f.get("rule"))]=f.get("status")
    return o
ab, asx = allset(base), allset(sim)
for k in sorted(set(ab)|set(asx), key=str):
    x,y = ab.get(k), asx.get(k)
    if x!=y: print(f"   {k}: {x} -> {y}")
