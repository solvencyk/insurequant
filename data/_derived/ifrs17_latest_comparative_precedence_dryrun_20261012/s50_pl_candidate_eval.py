"""Read-only dry run, PL_breakdown domain (Tier-1 = DART FS-API income-statement items) : current master vs LATEST comparative column.

Inputs   pl_tier1_scan.csv (s13) : per company x quarter x Tier-1 item - master / original filing / later filing's prior-year column
Unit     block = (company, quarter): all Tier-1 items 1,16..24,25..32 of that quarter are replaced TOGETHER or not at all.
Closure  of the Tier-1 sub-block (identities the production gate / owner rules apply to these items):
           I1  20 영업이익 = 1 보험손익 + 17 투자손익      tol max(0.1% x |20|, 200백만)    (validate_master_tables PL_EQS)
           I2  24 당기순이익 = 22 세전이익 - 23 법인세      tol max(0.1% x |24|, 200백만)    (PL_EQS)
           I3  31 총포괄손익 = 24 + 25 기타포괄손익         tol max(0.1% x |31|, 200백만)    (PL_OCI_TOTAL_IDENTITY, owner 2026-08-28)
           I4  17 투자손익 = 18 투자이익 + 19 보험금융손익   tol 200백만                      (PL_EQS; 18 is derived 17-19 -> tautology, listed as rule blind spot)
         The LOB legs (items 2..15) are Tier-2 note tables: NO prior-column reader exists for them, so a Tier-1 candidate can never be
         verified against the bridge "1 = sum of legs" -> blocks are reported as '후보 불완전' even when I1..I4 close.
Gold     company-quarter carrying an owner overlay cell (data/_gold/user_pl_cells.json) or an owner-confirmed cell -> 'gold 충돌'.
Kinds    SIGN_FLIP cells (|later| == |master|, opposite sign) are XBRL sign-convention noise and are NOT counted as restatements.
Output   pl_block_verdicts.csv
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lib_dryrun as D  # noqa: E402

ROOT = D.ROOT
scan = list(csv.DictReader(open(HERE / "pl_tier1_scan.csv", encoding="utf-8-sig")))
refined = {(r["kr"], r["quarter"], int(r["item"])): r["kind"] for r in csv.DictReader(open(HERE / "pl_tier1_scan_refined.csv", encoding="utf-8-sig"))}
pl = D.load_json("PL_breakdown.json")
M = defaultdict(dict)
NAMES = {}
for r in pl:
    M[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r["값"]
    NAMES[r["원보험사코드"]] = r["원수사명"]
gold = D.gold_pl_blocks()
confirmed = D.confirmed_pl_cells()
# bridge baseline (known failures) and source-absent keys
bridge = D.load_json("data/_gold/pl_bridge_baseline.json")["entries"]
bridge_keys = {(k.split("|")[0], k.split("|")[1]) for k in bridge}

TIER1 = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]


def f(x):
    try:
        return float(x)
    except Exception:
        return None


def ident(v):
    """returns dict identity -> (closed:boolean|None, residual)"""
    out = {}

    def chk(name, lhs, rhs_items, tol_abs=200.0, tol_rel=0.001):
        l = v.get(lhs)
        rs = [v.get(i) for i in rhs_items]
        if l is None or any(x is None for x in rs):
            out[name] = (None, None)
            return
        exp = sum(rs)
        res = l - exp
        out[name] = (abs(res) <= max(tol_rel * abs(l), tol_abs), round(res, 3))

    chk("I1_20=1+17", 20, [1, 17])
    # 24 = 22 - 23
    l, a, b = v.get(24), v.get(22), v.get(23)
    out["I2_24=22-23"] = (None, None) if None in (l, a, b) else (abs(l - (a - b)) <= max(0.001 * abs(l), 200.0), round(l - (a - b), 3))
    chk("I3_31=24+25", 31, [24, 25])
    chk("I4_17=18+19", 17, [18, 19], tol_abs=200.0, tol_rel=0.0)
    return out


# group scan cells by (kr, q)
blocks = defaultdict(dict)
for r in scan:
    blocks[(r["kr"], r["quarter"])][int(r["item"])] = r

out = []
cnt = Counter()
cells = Counter()
for (kr, q), items in sorted(blocks.items()):
    real = {it: r for it, r in items.items() if r["cls"] == "RESTATED_STALE" and refined.get((kr, q, it)) in ("REAL_SMALL", "REAL_LARGE")}
    flips = {it for it, r in items.items() if r["cls"] == "RESTATED_STALE" and refined.get((kr, q, it)) == "SIGN_FLIP"}
    adopted = {it for it, r in items.items() if r["cls"] == "RESTATED_ADOPTED"}
    neq = {it for it, r in items.items() if r["cls"] == "MASTER_NEQ_ORIG"}
    if not (real or adopted or neq or flips):
        continue
    cur = {it: M[(kr, q)].get(it) for it in TIER1}
    lat = dict(cur)
    for it, r in real.items():
        lat[it] = f(r["later"])
    noorig = [it for it, r in real.items() if r["basis_orig"] == "NO_ORIG_FSAPI"]
    row = {"domain": "PL_breakdown(Tier-1)", "kr": kr, "name": NAMES.get(kr, ""), "quarter": q,
           "orig_fsapi": "none(2023.1Q/2Q status 013: master = HTML fallback of the original filing)" if noorig else "yes",
           "later_filing_q": f"{int(q[:4])+1}{q[4:]}", "n_real_cells": len(real), "real_items": ",".join(map(str, sorted(real))),
           "n_sign_flip_cells": len(flips), "sign_flip_items": ",".join(map(str, sorted(flips))),
           "n_already_latest": len(adopted), "already_latest_items": ",".join(map(str, sorted(adopted))),
           "n_master_neq_orig": len(neq), "master_neq_items": ",".join(map(str, sorted(neq)))}
    # headline values
    for it in (1, 20, 22, 24):
        if it in real:
            row[f"item{it}_current"] = real[it]["master"]
            row[f"item{it}_latest"] = real[it]["later"]
    ic, il = ident(cur), ident(lat)
    row["identities_current"] = json.dumps({k: v[0] for k, v in ic.items()}, ensure_ascii=False)
    row["identities_latest"] = json.dumps({k: v[0] for k, v in il.items()}, ensure_ascii=False)
    closed_cur = all(v[0] is not False for v in ic.values())
    closed_lat = all(v[0] is not False for v in il.values())
    row["tier1_closed_current"] = closed_cur
    row["tier1_closed_latest"] = closed_lat
    row["bridge_baseline_current"] = (NAMES.get(kr, ""), q) in {(k.split("|")[0], k.split("|")[1]) for k in bridge}
    g = gold.get((kr, q))
    cf = confirmed.get((NAMES.get(kr, ""), q))
    row["gold_cells"] = ",".join(map(str, g)) if g else ""
    row["owner_confirmed_cells"] = json.dumps(cf, ensure_ascii=False) if cf else ""
    if g or cf:
        row["verdict"] = "gold 충돌"
    elif real:
        if closed_lat and closed_cur:
            row["verdict"] = "후보 불완전(Tier-1 닫힘/닫힘·LOB 다리 후보 없음)"
        elif closed_lat and not closed_cur:
            row["verdict"] = "후보 불완전(Tier-1 닫힘·현행 안 닫힘)"
        elif (not closed_lat) and closed_cur:
            row["verdict"] = "현행 유지(Tier-1 후보가 안 닫힘)"
        else:
            row["verdict"] = "둘 다 불가"
    elif adopted and not neq:
        row["verdict"] = "이미 최신(이전 라운드 채택)"
    elif neq:
        row["verdict"] = "마스터가 원본·최신 둘 다와 다름(오버라이드)"
    else:
        row["verdict"] = "부호 규약 차이만(재작성 아님)"
    out.append(row)
    cnt[row["verdict"]] += 1
    cells[row["verdict"]] += len(real)

cols = ["domain", "kr", "name", "quarter", "later_filing_q", "orig_fsapi", "n_real_cells", "real_items", "n_sign_flip_cells", "sign_flip_items", "n_already_latest",
        "already_latest_items", "n_master_neq_orig", "master_neq_items", "item1_current", "item1_latest", "item20_current", "item20_latest",
        "item22_current", "item22_latest", "item24_current", "item24_latest", "identities_current", "identities_latest", "tier1_closed_current",
        "tier1_closed_latest", "bridge_baseline_current", "gold_cells", "owner_confirmed_cells", "verdict"]
with open(HERE / "pl_block_verdicts.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(out)
print("PL Tier-1 blocks:", len(out), dict(cnt))
print("real changed cells by verdict:", dict(cells))
tot_blocks = len({(r['kr'], r['quarter']) for r in scan} | {(k[0], k[1]) for k in refined})
print("company-quarter blocks with a later comparative in the scan:", len({(r['kr'], r['quarter']) for r in scan if r['cls']}))
# blocks never touched (all SAME) can be counted from the scan summary file
print("identity closure current/latest among real-change blocks:",
      Counter((r["tier1_closed_current"], r["tier1_closed_latest"]) for r in out if r["n_real_cells"]))
