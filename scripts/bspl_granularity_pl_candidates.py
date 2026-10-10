#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B for PL_breakdown: candidate cells for items 1 (보험손익), 16 (기타사업비용), 22 (세전이익), 23 (법인세),
24 (당기순이익) from the management-disclosure summary PL (the only items the data-contract gate §3d lets the DISCLOSURE
lineage carry).  Blank master cells only; existing values are never touched.

Output: data/_derived/bspl_granularity_20261011/pl_candidates/<KR>.json
Run:    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_pl_candidates.py --company all|listed|KR..

Selection per (company, item, quarter), blank cells only
  1. own filing, summary PL column 0 (YTD)                      -- required: column identities do not fail
  2. year-end audit statement (exact 원) replaces the rounded 억원 value when both agree within 1.5억
  3. R1 (reinsurers, owner 2026-10-09): the NEXT YEAR's same-quarter summary PL column 1 (전년동기) wins over the own value
     when they differ (restatement); the later column must satisfy current - previous == change
  4. blank quarter with no own filing at all: filled from that same later column (any company, blank cells only)
Cross-checks: KPI staging (reinsurers, already R1-reconciled) +-1.5억; 24 = 22 - 23 inside the selected set.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import pl_stage as P  # noqa: E402
from bspl_granularity import stage_b as B  # noqa: E402

TIER2 = ["KR0004", "KR0029", "KR0049", "KR0050", "KR0051", "KR0074", "KR0075", "KR0076", "KR0080",
         "KR0095", "KR0097", "KR0100", "KR1010", "KR1011", "KR1098"]
REINS = ["KR1101", "KR1102", "KR1103", "KR1104", "KR1105", "KR1106", "KR1107", "KR1108"]
LISTED = ["KR0001", "KR0002", "KR0003", "KR0005", "KR0008", "KR0009", "KR0010", "KR0011", "KR0032", "KR0068",
          "KR0069", "KR0070", "KR0071", "KR0072", "KR0073", "KR0079", "KR0082", "KR0083", "KR0087", "KR0094",
          "KR0099", "KR0104", "KR0150", "KR1000"]
QUARTERS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
OUT = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "pl_candidates"
ITEMS = (1, 16, 22, 23, 24)
TOL = 150.0                     # 백만원 (= 1.5억: two roundings)
KPI_ITEM = {"보험손익": 1, "법인세비용차감전순이익": 22, "법인세": 23, "법인세비용": 23, "당기순이익": 24}


def next_year(q: str) -> str:
    return f"{int(q[:4]) + 1}.{q[5:]}"


def load_pl_master():
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    d = {}
    for r in rows:
        d[(r["원보험사코드"], str(r["항목번호"]), r["공시분기"])] = r["값"]
    return d


def load_kpi_pl(code):
    p = ROOT / "data" / "reinsurer" / f"kpi_summary_{code}.json"
    out = {}
    if not p.exists():
        return out
    d = json.loads(p.read_text(encoding="utf-8"))
    for r in d.get("rows", []):
        it = KPI_ITEM.get(r.get("metric"))
        v = r.get("value")
        if it and isinstance(v, (int, float)):
            out[(it, r["period"])] = float(v) * 100.0          # 억원 -> 백만원 (YTD)
    return out


def process(code, plm, no_anchor):
    docs, obs_all, notes = {}, [], []
    for q in QUARTERS:
        doc = B.load_tables(code, q)
        if doc is None:
            continue
        docs[q] = doc
        obs, nts = P.observations(doc, q)
        obs_all += obs
        notes += [f"{q} {n}" for n in nts]
    kpi = load_kpi_pl(code) if no_anchor else {}
    own = defaultdict(list)
    cmp_ = defaultdict(list)
    for o in obs_all:
        (own if o.col == 0 else cmp_)[(o.item, o.quarter)].append(o)

    def usable(o):
        if o.ident_ok is False:
            return False
        if o.kind == "sum_pl" and o.sem_ok is False:
            return False
        return True

    cands = []
    keys = sorted({k for k in list(own) + list(cmp_) if k[0] in ITEMS and k[1] in QUARTERS}, key=lambda k: (k[0], B.qkey(k[1])))
    for item, q in keys:
        mval = plm.get((code, str(item), q))
        o_list = [o for o in own.get((item, q), []) if usable(o)]
        c_list = [o for o in cmp_.get((item, q), []) if usable(o) and o.pdf_quarter == next_year(q)]
        rec = {"code": code, "item": item, "quarter": q}
        # --- choose the value ---
        pick, how, note = None, None, None
        sum_o = [o for o in o_list if o.kind == "sum_pl"]
        pf_o = [o for o in o_list if o.kind == "pl_full"]
        if sum_o and pf_o:
            if abs(sum_o[0].value_mn - pf_o[0].value_mn) <= TOL:
                pick, how = pf_o[0], "audit_exact"
            elif no_anchor and c_list and (abs(c_list[0].value_mn - sum_o[0].value_mn) <= TOL
                                           or abs(c_list[0].value_mn - pf_o[0].value_mn) <= TOL):
                # the summary and the audit statement disagree, the latest filing's comparative (R1) sides with one of them
                lo = c_list[0]
                pick, how = lo, "R1_tiebreak"
                note = (f"summary {sum_o[0].value_mn:.0f} vs audit {pf_o[0].value_mn:.0f} disagree; the later filing "
                        f"{lo.pdf_quarter} comparative decides")
            else:
                rec.update(status="HOLD_ALT_DISAGREE", value_mn=sum_o[0].value_mn, alt_mn=pf_o[0].value_mn)
                cands.append(rec)
                continue
        elif sum_o:
            pick, how = sum_o[0], "own_summary"
        elif pf_o:
            pick, how = pf_o[0], "audit_exact"
        r1 = None
        if c_list:
            lo = c_list[0]
            if pick is None:
                pick, how, note = lo, "later_comparative", f"no usable own value; {lo.pdf_quarter} summary PL 전년동기 column"
            elif no_anchor and abs(lo.value_mn - pick.value_mn) > max(TOL, 1.01 * pick.prec_mn):
                r1 = {"own_value_mn": pick.value_mn, "own_pdf_quarter": pick.pdf_quarter, "from": lo.pdf_quarter}
                pick, how, note = lo, "R1", f"R1: {lo.pdf_quarter} 전년동기 column replaces own {r1['own_value_mn']:.0f}"
        if pick is None:
            continue
        rec.update(value_mn=pick.value_mn, kind=pick.kind, page=pick.page, unit=pick.unit, prec_mn=pick.prec_mn, how=how,
                   note=note, pdf_quarter=pick.pdf_quarter, label=pick.label,
                   pdf=pick.src_pdf or docs[pick.pdf_quarter]["pdf"], sha256=pick.src_sha or docs[pick.pdf_quarter]["sha256"])
        if r1:
            rec["r1"] = r1
        # --- KPI cross-check (reinsurers) ---
        kv = kpi.get((item, q))
        if kv is not None:
            rec["kpi_mn"] = kv
            if abs(kv - pick.value_mn) > TOL:
                rec["status"] = "HOLD_KPI_DIFF"
                cands.append(rec)
                continue
        if mval is not None:
            rec["master"] = mval
            rec["status"] = "EXISTS_SAME" if abs(mval - pick.value_mn) <= max(TOL, 1.01 * pick.prec_mn) else "EXISTS_DIFF"
        else:
            rec["status"] = "CAND"
        cands.append(rec)
    # --- identity 24 = 22 - 23 inside the selected set (new cells + master values) ---
    sel = defaultdict(dict)
    for c in cands:
        if c["status"] in ("CAND", "EXISTS_SAME", "EXISTS_DIFF"):
            sel[c["quarter"]][c["item"]] = c["value_mn"] if c["status"] == "CAND" else c.get("master", c["value_mn"])
    for q, g in sel.items():
        for it in (22, 23, 24):
            if it not in g and plm.get((code, str(it), q)) is not None:
                g[it] = plm[(code, str(it), q)]
        if all(i in g for i in (22, 23, 24)) and abs(g[22] - g[23] - g[24]) > TOL:
            for c in cands:
                if c["quarter"] == q and c["status"] == "CAND" and c["item"] in (22, 23, 24):
                    c["status"] = "HOLD_IDENTITY"
                    c["identity"] = {"22": g[22], "23": g[23], "24": g[24], "resid": g[22] - g[23] - g[24]}
    return {"code": code, "candidates": cands, "notes": notes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--company", required=True)
    a = ap.parse_args()
    codes = (TIER2 + REINS if a.company == "all" else LISTED if a.company == "listed" else a.company.split(","))
    OUT.mkdir(parents=True, exist_ok=True)
    plm = load_pl_master()
    sbs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    for code in codes:
        res = process(code, plm, no_anchor=code in REINS)
        (OUT / f"{code}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        cnt = defaultdict(int)
        for c in res["candidates"]:
            cnt[c["status"]] += 1
        print(code, dict(cnt), flush=True)


if __name__ == "__main__":
    main()
