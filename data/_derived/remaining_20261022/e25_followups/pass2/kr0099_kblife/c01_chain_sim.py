# -*- coding: utf-8 -*-
"""READ-ONLY pass2 c01 (KR0099 KB라이프, ticket 20261024T0300Z item 7): would the CSM waterfall of 2024.1Q-2024.3Q at the LATEST comparative vector close the chain without an exception or pin?
Builds a TEMP copy of CSM_waterfall.json in which the 2024.1Q / 2Q / 3Q cumulative vectors of KR0099 (items 1, 3, 4, 5, 6; item 2 = 신계약 is equal in both vintages) are replaced by the FY2025 Q1 / H1 / Q3 report
prior-period values (separate basis, 백만원 -> 억원 = /100, master grid 1 decimal), then serves it to the live gates through gate_overlay (nothing in the repo is written).
Values (백만원, cells cited from the sweep rows data/_derived/remaining_20261022/e25_followups/sweep_neighbors*/mismatches*.csv and re-read at FY2025_Q1 L37618..L37818 in t01_FY2025_Q1_37587.txt):
  2024.1Q opening 3,179,826  이자 31,919  가정 -30,312  상각 -74,241  closing 3,238,551
  2024.2Q opening 3,179,826  이자 62,088  가정 -79,717  상각 -148,231 closing 3,241,352
  2024.3Q opening 3,179,826  이자 80,910  가정 -266,956 상각 -220,490 closing 3,146,268
The temp file is written to kr0099_kblife/csm_candidate_latest_2024.json; gates are run by the caller (run_chain_gates.sh)."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass2/kr0099_kblife/csm_candidate_latest_2024.json"
V = {
    "2024.1Q": {1: 3179826, 3: 31919, 4: -30312, 5: -74241, 6: 3238551},
    "2024.2Q": {1: 3179826, 3: 62088, 4: -79717, 5: -148231, 6: 3241352},
    "2024.3Q": {1: 3179826, 3: 80910, 4: -266956, 5: -220490, 6: 3146268},
}
rows = json.load(open(f"{ROOT}/CSM_waterfall.json", encoding="utf-8"))
by = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
chg = []
for q, d in V.items():
    for it, mn in d.items():
        r = by[("KR0099", it, q)]
        new = round(mn / 100.0, 1)
        chg.append((q, it, r["값"], new))
        r["값"] = new
        if it == 6:
            r["값_당분기"] = new
json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
for c in chg:
    print(f"  KR0099 {c[0]} item {c[1]}: {c[2]} -> {c[3]}")
# closure of the candidate vector (item 2 from the master)
for q in V:
    v = {i: by[("KR0099", i, q)]["값"] for i in range(1, 7)}
    print(f"  {q}: 기초 {v[1]} + 신계약 {v[2]} + 이자 {v[3]} + 가정 {v[4]} + 상각 {v[5]} = {v[1] + v[2] + v[3] + v[4] + v[5]:.1f} vs 기말 {v[6]}")
# boundary numbers
c4 = by[("KR0099", 6, "2023.4Q")]["값"]
print(f"  FY boundary: master 2023.4Q closing {c4} vs candidate 2024.1Q opening {by[('KR0099', 1, '2024.1Q')]['값']} -> gap {by[('KR0099', 1, '2024.1Q')]['값'] - c4:.1f}억 ({(by[('KR0099', 1, '2024.1Q')]['값'] - c4) / c4 * 100:.2f}%) ; tol = max({0.005 * c4:.1f}, 2.0)억")
c43 = by[("KR0099", 6, "2024.3Q")]["값"]
print(f"  2024.3Q candidate closing {c43} vs 2024.4Q master opening(값_당분기) {by[('KR0099', 1, '2024.4Q')]['값_당분기']}")
