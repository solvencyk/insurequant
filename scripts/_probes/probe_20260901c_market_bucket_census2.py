# -*- coding: utf-8 -*-
"""2026-09-01c (part2): odd-Q 138 missing buckets를 회사별로 분해.
같은 회사의 다른 odd-Q 에 item36 이 있으면(=그 회사는 홀수분기에도 세부표를 공시하는 관행)
이 특정 분기의 결측은 수상한 gap. 전혀 없으면 그 회사는 홀수분기 세부표를 아예 안 하는
관행일 가능성 -> case(c) 후보 (그래도 raw 확인 필요).
"""
import json
import io
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

idx = defaultdict(dict)
names = {}
for r in data:
    key = (r["원보험사코드"], r["공시분기"])
    idx[key][r["항목번호"]] = r.get("값")
    names[r["원보험사코드"]] = r["원수사명"]

odd_keys = [k for k in idx if not k[1].endswith(("2Q", "4Q"))]
by_company_odd = defaultdict(list)
for k in odd_keys:
    by_company_odd[k[0]].append(k[1])

miss36 = {k for k in idx if idx[k].get(36) is None}
miss36_odd_by_co = defaultdict(list)
for k in miss36:
    if not k[1].endswith(("2Q", "4Q")):
        miss36_odd_by_co[k[0]].append(k[1])

print(f"companies with >=1 odd-Q missing item36: {len(miss36_odd_by_co)}\n")

# categorize companies
never_disclose = []   # 0 odd-Q have item36 ever
partial = []           # some odd-Q have it, some don't (real gap candidates)
for co in sorted(miss36_odd_by_co, key=lambda c: names[c]):
    all_odd_q = sorted(by_company_odd[co])
    present_odd_q = sorted(q for q in all_odd_q if idx[(co, q)].get(36) is not None)
    missing_odd_q = sorted(miss36_odd_by_co[co])
    if present_odd_q:
        partial.append((co, names[co], missing_odd_q, present_odd_q))
    else:
        never_disclose.append((co, names[co], missing_odd_q))

print(f"=== category NEVER (odd-Q never has item36 in this company's history, n={len(never_disclose)} companies) ===")
tot = 0
for co, nm, missing_q in never_disclose:
    print(f"  {nm}({co}): missing odd-Q = {missing_q}  [all-odd-Q={sorted(by_company_odd[co])}]")
    tot += len(missing_q)
print(f"  subtotal cells = {tot}")

print(f"\n=== category PARTIAL (company DOES disclose in some odd-Q, missing in others -> gap candidate, n={len(partial)} companies) ===")
tot2 = 0
for co, nm, missing_q, present_q in partial:
    print(f"  {nm}({co}): missing={missing_q}  present={present_q}")
    tot2 += len(missing_q)
print(f"  subtotal cells = {tot2}")

print(f"\ngrand total = {tot + tot2} (should be 138)")
