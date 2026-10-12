"""Read-only: assemble the FULL latest-comparative PL block (items 1..24) of DB손해보험 2023.1Q-2023.3Q from the 2024.1Q-3Q filings and judge it.

  Tier-1 = production fetch_dart_fs._parse on the 2024 FS-API cache with thstrm<-frmtrm (prior-year column)
  Tier-2 = production extract_tier2_old with the comparative (전분기/전반기) tables selected (_old_prior flipped)
  items  = production build_pl_breakdown.assemble(t1, t2, is_life=False)         (no gold override, no RC gate: the raw assembled vector)
Judgement uses the gate arithmetic:  보험손익 bridge  1 = 2 + 13 + 14 + 15 - 16 (bare) or without 15/16 ; 영업이익 20 = 1 + 17 ; 세전 22 = 20 + 21 ; 순이익 24 = 22 - 23 ;
PL<->CSM amortisation identity  |PL 원수CSM상각(item 4)/100 - |CSM_waterfall item 5|| <= max(0.1억, 0.05%).
Writes db_pl_block_probe.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_dart_fs as F  # noqa: E402
import build_pl_breakdown as BP  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _iter_tables_by_basis, _tag_basis  # noqa: E402
from scripts.pl_breakdown import companies as C  # noqa: E402

CORP = "00159102"                               # DB손해보험
REPRT = {"1Q": "11013", "2Q": "11012", "3Q": "11014", "4Q": "11011"}
pl = {(r["공시분기"], r["항목번호"]): r["값"] for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8")) if r["원보험사코드"] == "KR0011"}
wf = {(r["공시분기"], r["항목번호"]): r["값"] for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")) if r["원보험사코드"] == "KR0011"}


def t1_prior(year, reprt, annual):
    for div in ("OFS", "CFS"):
        f = ROOT / "data/dart/_fs_api_cache" / f"{CORP}_{year}_{reprt}_{div}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        rows = []
        for a in d.get("list", []):
            b = dict(a)
            b["thstrm_amount"] = a.get("frmtrm_amount")
            b["thstrm_add_amount"] = a.get("frmtrm_add_amount")
            rows.append(b)
        t = F._parse({**d, "list": rows}, annual)
        if t:
            return t, div
    return None, None


def load_tables(rd):
    xs = sorted(set(list(rd.glob("*.xml")) + list(rd.glob("xml/*.xml"))), key=lambda p: p.stat().st_size, reverse=True)
    out = []
    for x in xs:
        out.extend(_tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
    return out


def ok(res, exp, tol_abs=200.0, tol_rel=0.001):
    """residual `res` is within the gate tolerance of the expected value `exp` (max(0.1% x |exp|, 200 백만원))."""
    return abs(res) <= max(tol_rel * abs(exp), tol_abs)


report = {}
cand_blocks = {}
for later, prior_q in (("2024.1Q", "2023.1Q"), ("2024.2Q", "2023.2Q"), ("2024.3Q", "2023.3Q")):
    qn = later[5] + "Q"
    t1, div = t1_prior(later[:4], REPRT[qn], False)
    rd = next((ROOT / "data/dart" / f"FY{later[:4]}_Q{later[5]}" / "raw").glob("KR0011_*"))
    tables = load_tables(rd)
    orig = C._old_prior
    C._old_prior = lambda tbls, i: not orig(tbls, i)
    try:
        t2 = C.extract_tier2_old(tables)
    finally:
        C._old_prior = orig
    v_lat = BP.assemble(t1, t2, False)
    v_cur = {i: pl.get((prior_q, i)) for i in range(1, 25)}

    def bridge(v):
        """returns dict of identity -> (closed, residual) in 백만원"""
        out = {}
        legs = [v.get(2), v.get(13), v.get(14)]
        if v.get(1) is not None and None not in legs:
            bare = sum(legs)
            adj = bare + (v.get(15) or 0) - (v.get(16) or 0)
            r_bare, r_adj = v[1] - bare, v[1] - adj
            out["B_1=2+13+14(+15-16)"] = (ok(r_bare, bare) or ok(r_adj, adj), round(min(r_bare, r_adj, key=abs), 1))
        if None not in (v.get(20), v.get(1), v.get(17)):
            out["I_20=1+17"] = (ok(v[20] - (v[1] + v[17]), v[20]), round(v[20] - (v[1] + v[17]), 1))
        if None not in (v.get(22), v.get(20), v.get(21)):
            out["I_22=20+21"] = (ok(v[22] - (v[20] + v[21]), v[22]), round(v[22] - (v[20] + v[21]), 1))
        if None not in (v.get(24), v.get(22), v.get(23)):
            out["I_24=22-23"] = (ok(v[24] - (v[22] - v[23]), v[24]), round(v[24] - (v[22] - v[23]), 1))
        l2 = [v.get(3), v.get(8)]
        if v.get(2) is not None and None not in l2:
            out["B_2=3+8"] = (ok(v[2] - sum(l2), v[2]), round(v[2] - sum(l2), 1))
        parts = [v.get(4), v.get(5), v.get(6), v.get(7)]
        if v.get(3) is not None and None not in parts:
            out["B_3=4+5+6+7"] = (ok(v[3] - sum(parts), v[3]), round(v[3] - sum(parts), 1))
        return out

    wf5 = wf.get((prior_q, 5))
    amort = lambda v: None if v.get(4) is None or wf5 is None else (abs(abs(v[4]) / 100.0 - abs(wf5)) <= max(0.1, 0.0005 * abs(wf5)), round(abs(v[4]) / 100.0 - abs(wf5), 2))
    br_c, br_l = bridge(v_cur), bridge(v_lat)
    print("=" * 110)
    print(f"{prior_q}  (latest comparative = {later} filing, basis {div})")
    keys = sorted({k for k in list(v_cur) + list(v_lat) if isinstance(k, int)})
    diff = [(k, v_cur.get(k), v_lat.get(k)) for k in keys if v_cur.get(k) != v_lat.get(k) and not (v_cur.get(k) is None and v_lat.get(k) is None)]
    print("  items that differ (item, current, latest):")
    for k, a, b in diff:
        print(f"     {k:>3}: {a!s:>14} -> {b!s:>14}")
    print("  bridge current:", {k: v for k, v in br_c.items()})
    print("  bridge latest :", {k: v for k, v in br_l.items()})
    print("  amortisation identity current (PL item4 vs CSM wf item5, 억):", amort(v_cur), " latest:", amort(v_lat), " wf(master)=", wf5)
    (HERE / "cand").mkdir(exist_ok=True)
    lat_all = {str(k): v_lat.get(k) for k in range(1, 33) if v_lat.get(k) is not None}
    cand_blocks[prior_q] = lat_all
    report[prior_q] = {"later": later, "basis": div, "differ": diff, "bridge_current": {k: list(v) for k, v in br_c.items()},
                       "bridge_latest": {k: list(v) for k, v in br_l.items()}, "amort_current": amort(v_cur), "amort_latest": amort(v_lat)}
(HERE / "db_pl_block_probe.json").write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")

(HERE / "cand" / "db_pl_block_lat.json").write_text(json.dumps(cand_blocks, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
