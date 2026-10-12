"""Read-only: candidate insurance_liability_portfolio.json in which the 하나생명(KR0097) 2024.4Q accounting-model block (items 1-7, 8 = their sum) is replaced by the LATEST
comparative print (FY2025 결산 4-6-2 '<2024년>' table, whole 억원) and the Hana CSM waterfall closing check (3+6 vs waterfall item 6).  Output cand/insurance_liability_portfolio.ILP.json"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ilp = json.loads((ROOT / "insurance_liability_portfolio.json").read_text(encoding="utf-8"))
idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in ilp}
cen = [r for r in csv.DictReader(open(HERE / "ilp_yearend_2024_census.csv", encoding="utf-8-sig")) if r["kr"] == "KR0097" and r["quarter"] == "2024.4Q"][0]
lat = json.loads(cen["latest"])
cur = [idx[("KR0097", i, "2024.4Q")]["값"] for i in range(1, 9)]
print("master items 1-8:", cur, "sum1-7", round(sum(cur[:7]), 4))
print("latest items 1-7:", lat, "sum", sum(lat))
for i in range(1, 8):
    idx[("KR0097", i, "2024.4Q")]["값"] = float(lat[i - 1])
idx[("KR0097", 8, "2024.4Q")]["값"] = float(sum(lat))
(HERE / "cand" / "insurance_liability_portfolio.ILP.json").write_text(json.dumps(ilp, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
wf = {r["항목번호"]: r["값"] for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")) if r["원보험사코드"] == "KR0097" and r["공시분기"] == "2024.4Q"}
print("waterfall 2024.4Q closing (item 6, 억):", wf.get(6), "| ILP 3+6 master:", round(cur[2] + cur[5], 4), "latest:", lat[2] + lat[5])
