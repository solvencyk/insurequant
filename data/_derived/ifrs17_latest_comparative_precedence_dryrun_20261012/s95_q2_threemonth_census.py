"""Read-only census: 2023.2Q PL Tier-1 cells (items 1/20/22/23/24) - does the master value equal the 3-MONTH amount instead of the 6-month cumulative?
Reference (FS-API cache, comparative columns of the 2024 filings, restated basis):  cum2 = 6-month cumulative (2024.2Q filing, frmtrm_add_amount),
cum1 = 3-month cumulative (2024.1Q filing, frmtrm_add_amount), so the 2Q-only amount = cum2 - cum1.
Class: 3M_COLUMN?  master within 8% of (cum2-cum1) AND farther than 12% from cum2 ;  CUM_OK  master within 3% of cum2 ;  CUM_RESTATED  within 25% ; OTHER.
Output q2_threemonth_census.csv"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import plprior as P  # noqa: E402

HERE, ROOT, F = P.HERE, P.ROOT, P.F
M, NAMES = {}, {}
for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8")):
    M[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r["값"]
    NAMES[r["원보험사코드"]] = r["원수사명"]


def comparative(corp, year, reprt):
    for div in ("OFS", "CFS"):
        t, dv = P.t1_prior(corp, year, reprt, divs=(div,))
        if t:
            return t, dv
    return None, None


rows = []
for kr in sorted({k[0] for k in M}):
    corp2 = P.corp_of(kr, "FY2024_Q2")
    corp1 = P.corp_of(kr, "FY2024_Q1")
    if not corp2 or not corp1:
        continue
    c2, d2 = comparative(corp2, "2024", "11012")
    c1, d1 = comparative(corp1, "2024", "11013")
    if not c2 or not c1:
        continue
    orig = ROOT / "data/dart/_fs_api_cache" / f"{corp2}_2023_11012_OFS.json"
    has_orig = orig.exists() and orig.stat().st_size > 200
    for it in (1, 20, 22, 23, 24):
        mv, cv2, cv1 = M.get((kr, "2023.2Q", it)), c2.get(it), c1.get(it)
        if None in (mv, cv2, cv1) or abs(cv2) < 1:
            continue
        tv = cv2 - cv1
        near_cum = abs(mv / cv2 - 1)
        near_m3 = abs(mv / tv - 1) if abs(tv) >= 1 else 9.9
        cls = "3M_COLUMN?" if (near_m3 < 0.08 and near_cum > 0.12) else ("CUM_OK" if near_cum < 0.03 else ("CUM_RESTATED" if near_cum < 0.25 else "OTHER"))
        rows.append({"kr": kr, "name": NAMES.get(kr), "item": it, "master": round(mv, 3), "latest_cum6m": round(cv2, 3), "latest_2q_only": round(tv, 3), "near_cum": round(near_cum, 4), "near_3m": round(near_m3, 4),
                     "orig_fsapi": has_orig, "basis": d2, "cls": cls})
cols = ["kr", "name", "item", "master", "latest_cum6m", "latest_2q_only", "near_cum", "near_3m", "orig_fsapi", "basis", "cls"]
with open(HERE / "q2_threemonth_census.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
print("cells", len(rows), dict(Counter((r["cls"], r["orig_fsapi"]) for r in rows)))
print("3M_COLUMN? candidates:")
for r in rows:
    if r["cls"] == "3M_COLUMN?":
        print("  ", r["kr"], str(r["name"])[:8], "item", r["item"], "master", r["master"], "cum6m", r["latest_cum6m"], "2q-only", r["latest_2q_only"], "orig_fsapi", r["orig_fsapi"])
