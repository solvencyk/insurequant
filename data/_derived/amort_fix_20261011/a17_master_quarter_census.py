# -*- coding: utf-8 -*-
"""a17 (read-only): census of EVERY (company, quarter) cell of CSM_amortization.json for the prior-year-table defect.

 1. DART-derived cells (2025.4Q, built from the viz panel): does the master vector y1..y10 equal the 2024-12-31 schedule, i.e. the CURRENT-year
    schedule of the same company's FY2024 filing (data/dart/extracted, FY2024 rcept)?  Run on the PRE-FIX master (backup) and on the fixed master.
 2. Quarters that do not come from the DART panel (2023.4Q / 2024.4Q reinsurers, Lina 2025.3Q / 2026.1Q / 2026.2Q): never touched by
    _pick_amort_block; checked only for duplicated vectors across the quarters of one company.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
sys.stdout.reconfigure(encoding="utf-8")

ALIAS = {"미래에셋생명": "미래에셋생명보험", "삼성생명": "삼성생명보험", "코리안리": "코리안리재보험", "아이비케이연금보험": "IBK연금보험",
         "케이비라이프생명보험": "KB라이프생명", "에이아이지손해보험": "AIG손해보험", "엠지손해보험": "예별손해보험"}


def vectors(rows):
    out = defaultdict(dict)
    for r in rows:
        out[(r["원수사명"], r["공시분기"])][r["경과차년"]] = r["상각액"]
    return {k: [v.get(i) for i in range(1, 11)] for k, v in out.items()}


def near(a, b, tol=0.06):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    return len(pairs) >= 5 and all(abs(x - y) <= tol for x, y in pairs)


pre_rows = json.loads((ROOT / "data/_derived/amort_fix_backup_20261011/CSM_amortization.json.pre_fix").read_text(encoding="utf-8"))
now_rows = json.loads((ROOT / "CSM_amortization.json").read_text(encoding="utf-8"))
after = json.loads((W / "a08_selection_after.json").read_text(encoding="utf-8"))
# the 2024-12-31 schedule = result of the company's FY2024 filing (rcept 2025...), selected with the fixed picker
fy24 = {}
for fn, rec in after.items():
    if rec["rcept"].startswith("2025") and rec["result"] and rec["result"].get("status") == "ok":
        y = rec["result"].get("yearly") or {}
        fy24.setdefault(rec["company"], []).append((rec["rcept"], [y.get(f"y{k}") for k in range(1, 11)]))

for label, rows in (("PRE-FIX master", pre_rows), ("FIXED master", now_rows)):
    vec = vectors(rows)
    flagged = []
    checked = 0
    for (nm, q), v in sorted(vec.items()):
        if q != "2025.4Q":
            continue
        co = next((c for c in fy24 if ALIAS.get(c, c) == nm), None)
        if co is None:
            continue
        checked += 1
        if any(near(v, w) for _, w in fy24[co]):
            flagged.append(nm)
    print(f"1. {label}: 2025.4Q cells compared with the same company's FY2024-filing current schedule: {checked} | cell == 2024-12-31 schedule: {len(flagged)}")
    print("   ", flagged)

vec = vectors(now_rows)
by_co = defaultdict(list)
for (nm, q), v in vec.items():
    by_co[nm].append((q, v))
dups = []
for nm, lst in by_co.items():
    lst.sort()
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            if near(lst[i][1], lst[j][1], tol=1e-9):
                dups.append((nm, lst[i][0], lst[j][0]))
print("2. quarters in the fixed master:", sorted({q for (_, q) in vec}), "| cells per quarter:", {q: sum(1 for (_, qq) in vec if qq == q) for q in sorted({q for (_, q) in vec})})
print("   identical vectors across two quarters of one company:", dups)
