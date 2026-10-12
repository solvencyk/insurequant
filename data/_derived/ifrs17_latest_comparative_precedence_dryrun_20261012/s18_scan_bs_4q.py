"""Read-only census (offline): IFRS17_BS year-end (4Q) main items - master vs original FS-API vs LATEST comparative (next annual's frmtrm).

Items (master 항목번호 -> account_id): 1 Assets, 2 Liabilities, 3 Equity, 4 AOCI, 14 ReinsuranceContractsHeldThatAreAssets,
20 InsuranceContractsIssuedThatAreLiabilities, 21 ReinsuranceContractsHeldThatAreLiabilities, 30 IssuedCapital, 31 RetainedEarnings.
Master unit = 백만원 (cache 원 / 1e6).  Basis OFS first, CFS fallback (as build_ifrs17_bs does).
Output: bs_4q_scan.csv  (rows where master != later)  + printed class counts.
class: SAME_ALL | RESTATED_STALE (master==orig!=later) | RESTATED_ADOPTED (master==later!=orig) | MASTER_NEQ_ORIG
"""
from __future__ import annotations

import csv
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / "data/dart/_fs_api_cache"
ACC = {1: "ifrs-full_Assets", 2: "ifrs-full_Liabilities", 3: "ifrs-full_Equity", 4: "ifrs-full_AccumulatedOtherComprehensiveIncome",
       14: "ifrs-full_ReinsuranceContractsHeldThatAreAssets", 20: "ifrs-full_InsuranceContractsIssuedThatAreLiabilities",
       21: "ifrs-full_ReinsuranceContractsHeldThatAreLiabilities", 30: "ifrs-full_IssuedCapital", 31: "ifrs-full_RetainedEarnings"}

corp2kr = {}
for m in glob.glob(str(ROOT / "data/dart/FY*_Q*/raw/KR*/meta.json")):
    try:
        j = json.loads(Path(m).read_text(encoding="utf-8"))
    except Exception:
        continue
    if j.get("corp_code"):
        corp2kr[j["corp_code"]] = Path(m).parent.name.split("_")[0]

bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
MB = {}
NAMES = {}
for r in bs:
    MB[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r["값"]
    NAMES[r["원보험사코드"]] = r["원수사명"]


def load(corp, year, div):
    f = CACHE / f"{corp}_{year}_11011_{div}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def vals(d, field):
    out = {}
    if not d:
        return out
    for a in d.get("list", []):
        if a.get("sj_div") != "BS":
            continue
        aid = a.get("account_id") or ""
        if aid in ACC.values() and aid not in out:
            try:
                out[aid] = float(a.get(field)) / 1e6
            except Exception:
                pass
    return out


def same(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= max(1.0, 1e-5 * max(abs(a), abs(b)))


rows, cnt = [], Counter()
blocks = defaultdict(Counter)
corps = sorted({Path(f).name.split("_")[0] for f in CACHE.glob("*.json")})
for corp in corps:
    kr = corp2kr.get(corp)
    if not kr:
        continue
    for y in (2022, 2023, 2024, 2025):
        for div in ("OFS", "CFS"):
            d0, d1 = load(corp, y, div), load(corp, y + 1, div)
            if d0 and d1:
                break
        else:
            continue
        o = vals(d0, "thstrm_amount")
        l = vals(d1, "frmtrm_amount")
        if not o or not l:
            continue
        q = f"{y}.4Q"
        for it, aid in ACC.items():
            ov, lv, mv = o.get(aid), l.get(aid), MB.get((kr, q, it))
            if ov is None and lv is None:
                continue
            if same(mv, ov) and same(ov, lv):
                cnt["SAME_ALL"] += 1
                blocks[(kr, q)]["SAME"] += 1
                continue
            if not same(mv, ov):
                cls = "RESTATED_ADOPTED" if (same(mv, lv) and not same(ov, lv)) else "MASTER_NEQ_ORIG"
            else:
                cls = "RESTATED_STALE"
            cnt[cls] += 1
            blocks[(kr, q)][cls] += 1
            _rc = next((a.get("rcept_no") for a in (d1 or {}).get("list", []) if a.get("rcept_no")), None)
            rows.append({"kr": kr, "name": NAMES.get(kr, ""), "quarter": q, "item": it, "account": aid, "master": mv, "orig": ov, "later": lv, "basis": div, "cls": cls,
                         "later_rcept": _rc, "later_file": f"data/dart/_fs_api_cache/{corp}_{y+1}_11011_{div}.json"})
with open(HERE / "bs_4q_scan.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["kr", "name", "quarter", "item", "account", "master", "orig", "later", "basis", "cls", "later_rcept", "later_file"])
    w.writeheader()
    w.writerows(rows)
print(dict(cnt))
bl = Counter()
for k, c in blocks.items():
    for kk in c:
        if kk != "SAME":
            bl[kk] += 1
print("blocks:", dict(bl), "of", len(blocks))
for r in rows:
    if r["cls"] in ("RESTATED_STALE", "RESTATED_ADOPTED") and r["item"] in (1, 2, 3, 20):
        print(r["kr"], r["name"][:6], r["quarter"], "item", r["item"], "master", r["master"], "orig", r["orig"], "later", r["later"], r["cls"])

import json as _json
_json.dump({"cells": dict(cnt), "blocks_with_class": dict(bl), "year_end_blocks_with_later_annual": len(blocks)},
           open(HERE / "bs_4q_scan_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
