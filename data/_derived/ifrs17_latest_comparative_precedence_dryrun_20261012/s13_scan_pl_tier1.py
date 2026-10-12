"""Read-only census (offline): PL Tier-1 items - master vs original filing vs LATEST comparative column.

Uses the production parser scripts/fetch_dart_fs._parse() UNCHANGED on the committed FS-API cache (data/dart/_fs_api_cache, no network):
  orig  = _parse(cache[corp, Y, reprt, fs_div])                     (what the master was built from)
  later = _parse(cache[corp, Y+1, reprt, fs_div] with thstrm<-frmtrm) (the later filing's comparative column for the same period)
basis: OFS first, CFS fallback (same order as tier1_for).
Tier-1 items checked (master 항목번호): 1 17 19 20 21 22 23 24 | 16 | 25..32 (OCI) | 18
Output: pl_tier1_scan.csv (one row per company x quarter x item where any of the three differ) + pl_tier1_scan_summary.json

classification per cell:
  SAME_ALL           master == orig == later (within tol)         -> not written
  MASTER_NEQ_ORIG    master != orig (gold / handler / override)    (later may or may not equal)
  RESTATED_STALE     master == orig, later differs                 -> master is on the ORIGINAL filing, latest comparative differs
  RESTATED_ADOPTED   master == later != orig                       -> master already carries the later (restated) value
  NO_LATER           no later comparative available                -> not written
tolerance: max(0.01 백만원 abs ... 1.0 백만원, 0.001%): the cache is in 원 -> 백만원 with 6 dp.
"""
from __future__ import annotations

import csv
import glob
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.chdir(ROOT)                      # fetch_dart_fs uses cwd-relative paths
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_dart_fs as F  # noqa: E402  (import has no network side effect; we never call _fetch_raw)

CACHE = ROOT / "data/dart/_fs_api_cache"
ITEMS = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]

# corp_code -> KR code from raw meta.json
corp2kr = {}
for m in glob.glob(str(ROOT / "data/dart/FY*_Q*/raw/KR*/meta.json")):
    try:
        j = json.loads(Path(m).read_text(encoding="utf-8"))
    except Exception:
        continue
    kr = Path(m).parent.name.split("_")[0]
    if j.get("corp_code"):
        corp2kr[j["corp_code"]] = kr

pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
MP = {}
NAMES = {}
for r in pl:
    MP[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r["값"]
    NAMES[r["원보험사코드"]] = r["원수사명"]

REPRT = {"1Q": "11013", "2Q": "11012", "3Q": "11014", "4Q": "11011"}


def load(corp, year, reprt, fs_div):
    f = CACHE / f"{corp}_{year}_{reprt}_{fs_div}.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def swap(d):
    rows = []
    for a in d.get("list", []):
        b = dict(a)
        b["thstrm_amount"] = a.get("frmtrm_amount")
        b["thstrm_add_amount"] = a.get("frmtrm_add_amount")
        rows.append(b)
    return {**d, "list": rows}


def parse(d, annual):
    if not d:
        return None
    try:
        return F._parse(d, annual)
    except Exception:
        return None


def rcept(corp, year, reprt, fs_div):
    d = load(corp, year, reprt, fs_div)
    for a in (d or {}).get("list", []):
        if a.get("rcept_no"):
            return a["rcept_no"]
    return None


def tier1(corp, year, reprt, annual, later=False):
    for fs_div in ("OFS", "CFS"):
        d = load(corp, year, reprt, fs_div)
        if d is None:
            continue
        t = parse(swap(d) if later else d, annual)
        if t:
            return t, fs_div
    return None, None


def same(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= max(1.0, 1e-5 * max(abs(a), abs(b)))


def main():
    out = []
    summ = Counter()
    per_kq = defaultdict(lambda: Counter())
    corps = sorted({Path(f).name.split("_")[0] for f in CACHE.glob("*.json")})
    for corp in corps:
        kr = corp2kr.get(corp)
        if not kr:
            continue
        for y in (2023, 2024, 2025):
            for qn in (1, 2, 3, 4):
                q = f"{y}.{qn}Q"
                reprt = REPRT[f"{qn}Q"]
                annual = qn == 4
                orig, fs1 = tier1(corp, str(y), reprt, annual)
                later, fs2 = tier1(corp, str(y + 1), reprt, annual, later=True)
                no_orig = orig is None
                if no_orig:
                    # 2023.1Q/2Q: FS-API status 013 (no data) - the master came from the HTML fallback of the ORIGINAL filing; compare master vs later only
                    if later is None:
                        continue
                    orig, fs1 = {}, "NO_ORIG_FSAPI"
                if later is None:
                    summ["NO_LATER_blocks"] += 1
                    continue
                for it in ITEMS:
                    mv = MP.get((kr, q, it))
                    ov = orig.get(it)
                    lv = later.get(it)
                    if mv is None and ov is None and lv is None:
                        continue
                    if no_orig:
                        if mv is None:
                            cls = "ONLY_LATER"
                        elif same(mv, lv):
                            summ["SAME_ALL_noorig"] += 1
                            per_kq[(kr, q)]["SAME"] += 1
                            continue
                        else:
                            cls = "RESTATED_STALE"
                    elif mv is None and ov is None:
                        cls = "ONLY_LATER"
                    elif same(mv, ov) and same(ov, lv):
                        summ["SAME_ALL"] += 1
                        per_kq[(kr, q)]["SAME"] += 1
                        continue
                    elif not same(mv, ov):
                        cls = "MASTER_NEQ_ORIG" + ("" if same(mv, lv) else "")
                        if same(mv, lv) and not same(ov, lv):
                            cls = "RESTATED_ADOPTED"
                    elif same(mv, ov) and not same(ov, lv):
                        cls = "RESTATED_STALE"
                    else:
                        cls = "OTHER"
                    summ[cls] += 1
                    per_kq[(kr, q)][cls] += 1
                    out.append({"kr": kr, "name": NAMES.get(kr, ""), "quarter": q, "later_q": f"{y+1}.{qn}Q", "item": it,
                                "master": mv, "orig": ov, "later": lv, "basis_orig": fs1, "basis_later": fs2, "cls": cls,
                                "later_rcept": rcept(corp, str(y + 1), reprt, fs2),
                                "later_file": f"data/dart/_fs_api_cache/{corp}_{y+1}_{reprt}_{fs2}.json"})
    cols = ["kr", "name", "quarter", "later_q", "item", "master", "orig", "later", "basis_orig", "basis_later", "cls", "later_rcept", "later_file"]
    with open(HERE / "pl_tier1_scan.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    blocks = Counter()
    for (kr, q), c in per_kq.items():
        for k in c:
            if k != "SAME":
                blocks[k] += 1
    json.dump({"cells": dict(summ), "blocks_with_class": dict(blocks), "company_quarters": len(per_kq)},
              open(HERE / "pl_tier1_scan_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(dict(summ))
    print("blocks with at least one cell of class:", dict(blocks), "of", len(per_kq), "company-quarters")


if __name__ == "__main__":
    main()
