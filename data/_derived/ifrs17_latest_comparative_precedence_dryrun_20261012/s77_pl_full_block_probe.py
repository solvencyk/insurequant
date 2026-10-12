"""Read-only: assemble the FULL latest-comparative PL block (items 1..32) of 2023.1Q-3Q for non-life companies whose Tier-2 chain can be flipped to the
comparative columns (s71 generalised; see s76 for the flip technique), judge it with the gate arithmetic and write cand/pl_block_lat_<KR>.json.

usage: python s77_pl_full_block_probe.py KR0008 KR0001 ...
Judgement (백만원): bridge 1 = 2+13+14 (bare) or +15-16 (adj) ; 20 = 1+17 ; 22 = 20+21 ; 24 = 22-23 ; 3 = 4+5+6+7 ; 2 = 3+8 ;
amortisation identity |PL item4/100 - |CSM wf item5 (latest overlay or master)|| <= max(0.1억, 0.05%).
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
import build_pl_breakdown as BP  # noqa: E402
import fetch_dart_fs as F  # noqa: E402
from scripts.pl_breakdown import companies as C  # noqa: E402
from scripts.pl_breakdown import tier2 as T2  # noqa: E402

REPRT = {"1Q": "11013", "2Q": "11012", "3Q": "11014", "4Q": "11011"}
M = {}
for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8")):
    M[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r["값"]
NAMES = {}
WF5 = {}
for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")):
    NAMES[r["원보험사코드"]] = r["원수사명"]
    if r["항목번호"] == 5:
        WF5[(r["원보험사코드"], r["공시분기"])] = r["값"]
OV = json.loads((HERE / "cand" / "csm_adopt_overlay.json").read_text(encoding="utf-8"))
ALL = json.loads((HERE / "cand" / "CSM_waterfall.ALLTRUSTED.json").read_text(encoding="utf-8"))
WF5_LAT = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in ALL if r["항목번호"] == 5}      # latest CSM amort where a trusted prior-column vector exists
LIFE = {"KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0073", "KR0079", "KR0082", "KR0083", "KR0087", "KR0094", "KR0099", "KR0104"}
_orig_old_prior = C._old_prior
_orig_b = T2._b_note_table


def second_b(tables):
    seen = 0
    for t in tables:
        if "보험손익" in (t.caption or "") and "상세내역" in (t.caption or ""):
            if any(T2._row_matches(r, T2.B_CSM) for r in t.rows):
                seen += 1
                if seen == 2:
                    return t
    return None


def corp_of(kr, fy):
    for d in sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*")):
        mp = d / "meta.json"
        if mp.exists():
            return json.loads(mp.read_text(encoding="utf-8")).get("corp_code")
    return None


def t1_prior(corp, year, reprt):
    for div in ("OFS", "CFS"):
        f = ROOT / "data/dart/_fs_api_cache" / f"{corp}_{year}_{reprt}_{div}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        rows = []
        for a in d.get("list", []):
            b = dict(a)
            b["thstrm_amount"] = a.get("frmtrm_amount")
            b["thstrm_add_amount"] = a.get("frmtrm_add_amount")
            rows.append(b)
        t = F._parse({**d, "list": rows}, False)
        if t:
            return t, div
    return None, None


def closed(res, exp, tol_abs=200.0, tol_rel=0.001):
    return abs(res) <= max(tol_rel * abs(exp), tol_abs)


def bridge(v):
    out = {}
    legs = [v.get(2), v.get(13), v.get(14)]
    if v.get(1) is not None and None not in legs:
        bare = sum(legs)
        adj = bare + (v.get(15) or 0) - (v.get(16) or 0)
        rb, ra = v[1] - bare, v[1] - adj
        out["B1_1=2+13+14(+15-16)"] = (closed(rb, bare) or closed(ra, adj), round(min(rb, ra, key=abs), 1))
    for name, l, rs, sg in (("I_20=1+17", 20, (1, 17), 1), ("I_22=20+21", 22, (20, 21), 1)):
        if v.get(l) is not None and all(v.get(i) is not None for i in rs):
            res = v[l] - sum(v[i] for i in rs)
            out[name] = (closed(res, v[l]), round(res, 1))
    if None not in (v.get(24), v.get(22), v.get(23)):
        res = v[24] - (v[22] - v[23])
        out["I_24=22-23"] = (closed(res, v[24]), round(res, 1))
    if v.get(3) is not None and None not in (v.get(4), v.get(5), v.get(6), v.get(7)):
        res = v[3] - (v[4] + v[5] + v[6] + v[7])
        out["B_3=4+5+6+7"] = (closed(res, v[3]), round(res, 1))
    return out


report = {}
for kr in sys.argv[1:]:
    is_life = kr in LIFE
    for later, prior_q in (("2024.1Q", "2023.1Q"), ("2024.2Q", "2023.2Q"), ("2024.3Q", "2023.3Q")):
        fy = f"FY{later[:4]}_Q{later[5]}"
        dirs = [str(d) for d in sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*"))]
        corp = corp_of(kr, fy)
        t1, div = t1_prior(corp, later[:4], REPRT[later[5] + "Q"])
        C._old_prior = lambda tbls, i, _o=_orig_old_prior: not _o(tbls, i)
        T2._b_note_table = second_b
        try:
            _t1x, t2 = BP.parse_filing(dirs, is_life, kr, NAMES.get(kr), later)
        finally:
            C._old_prior = _orig_old_prior
            T2._b_note_table = _orig_b
        v_lat = BP.assemble(t1, t2, is_life)
        v_cur = {i: M.get((kr, prior_q, i)) for i in range(1, 33)}
        wf_lat = WF5_LAT.get((kr, prior_q))
        wf_cur = WF5.get((kr, prior_q))

        def amort(v, wf):
            if v.get(4) is None or wf is None:
                return None
            r = abs(v[4]) / 100.0 - abs(wf)
            return (abs(r) <= max(0.1, 0.0005 * abs(wf)), round(r, 2))

        print("=" * 110)
        print(f"{kr} {NAMES.get(kr)} {prior_q}  (latest comparative = {later} filing; Tier-1 basis {div})")
        print("   bridge current :", {k: v for k, v in bridge(v_cur).items()})
        print("   bridge latest  :", {k: v for k, v in bridge(v_lat).items()})
        print("   amort identity: current PL vs CSM master wf:", amort(v_cur, wf_cur), " | latest PL vs latest CSM wf:", amort(v_lat, wf_lat), " | latest PL vs master wf:", amort(v_lat, wf_cur))
        diff = {k: (v_cur.get(k), v_lat.get(k)) for k in range(1, 33) if v_cur.get(k) != v_lat.get(k) and v_lat.get(k) is not None}
        print("   items changed:", len(diff))
        report[f"{kr}|{prior_q}"] = {"later": later, "tier1_basis": div, "latest_block": {str(k): v_lat.get(k) for k in range(1, 33) if v_lat.get(k) is not None},
                                      "bridge_current": {k: list(v) for k, v in bridge(v_cur).items()}, "bridge_latest": {k: list(v) for k, v in bridge(v_lat).items()},
                                      "amort_current": amort(v_cur, wf_cur), "amort_latest_vs_latest_wf": amort(v_lat, wf_lat), "n_items_changed": len(diff)}
(HERE / "cand" / "pl_block_lat_probe.json").write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")
