#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 4: 처브라이프 (KR0100) BS item 20 (보험계약부채) — the two definitions side by side.

For every quarter the filing's own 8-1 statement gives
  D1  일반계정 보험계약부채   (supervisory form: 보험계약부채 of the general account)
  SA  특별계정부채            (supervisory form only; the K-IFRS audit statement has no such line)
  D2  D1 + SA                 (what the K-IFRS 보험계약부채 line of the audited year-end statements and of DART's
                               ifrs-full_InsuranceContractsIssuedThatAreLiabilities contains)
  책임준비금 (supervisory summary BS) = D1 + 재보험계약부채 + 투자계약부채  (general account only)
next to the master cell and its provenance.  Read-only.   Output: data/_derived/bspl_followup_20261011/kr0100_item20_definitions.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402
from bspl_granularity.views import view_all, col  # noqa: E402

CODE = "KR0100"
QS = ["2022.4Q"] + [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "kr0100_item20_definitions.json"


def grab(t, ci):
    va = view_all(t)
    f = B.UNIT_FACTOR.get(t.get("unit"))
    if f is None:
        return None
    def g(k):
        if k not in va:
            return None
        v = col(va[k][0], ci)
        return None if v is None else v * f
    return {"D1_보험계약부채": g("보험계약부채"), "SA_특별계정부채": g("특별계정부채"), "재보험계약부채": g("재보험계약부채"),
            "투자계약부채": g("투자계약부채"), "책임준비금": g("책임준비금"), "부채총계": g("부채총계"), "unit": t.get("unit"), "page": t["page"]}


def main():
    all_v, anchor, disc, meta = B.load_master()
    mv = all_v[CODE]
    side = json.loads((ROOT / "data" / "_derived" / "bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]
    rows = []
    for q in QS:
        rec = {"quarter": q, "master20": mv.get((20, q)), "master_source": ("경영공시 사이드카" if f"{CODE}|20|{q}" in side else "DART/감사보고서 빌더" if mv.get((20, q)) is not None else None),
               "from_own_filing": None, "from_next_filings_prior_year_end": []}
        doc = B.load_tables(CODE, q)
        if doc:
            ts = B.pick_tables(doc, "bs_full")
            if ts:
                rec["from_own_filing"] = grab(ts[0], 0)
                rec["own_table_kind"] = "K(감사/연말)" if B.table_form(ts[0]) == "K" else "S(감독서식 8-1)"
            sb = [t for t in doc["tables"] if t["kind"] == "sum_bs"]
            if sb:
                va = view_all(sb[0])
                f = B.UNIT_FACTOR.get(sb[0].get("unit"))
                if f and "책임준비금" in va:
                    v = col(va["책임준비금"][0], 0)
                    rec["summary_책임준비금_일반계정"] = None if v is None else v * f
        rows.append(rec)
    # year-end anchors seen in later filings (prior-year-end column of the next filings' 8-1)
    for q in QS:
        if not q.endswith("4Q"):
            continue
        for q2 in QS:
            if B.qkey(q2) <= B.qkey(q):
                continue
            doc = B.load_tables(CODE, q2)
            if not doc:
                continue
            ts = B.pick_tables(doc, "bs_full")
            if ts and B._has_cols(ts[0], 2):
                g = grab(ts[0], 1)
                if g and g["D1_보험계약부채"] is not None:
                    next(r for r in rows if r["quarter"] == q)["from_next_filings_prior_year_end"].append({"filing": q2, **g})
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"{'quarter':8} {'master':>14} {'src':<10} {'D1 일반계정':>14} {'SA 특별계정':>12} {'D2=D1+SA':>14} {'재보험':>10} {'책임준비금(요약)':>16}  match")
    for r in rows:
        o = r["from_own_filing"] or {}
        d1, sa = o.get("D1_보험계약부채"), o.get("SA_특별계정부채")
        d2 = (d1 + sa) if (d1 is not None and sa is not None) else None
        m = r["master20"]
        tag = ""
        if m is not None:
            if d1 is not None and abs(m - d1) <= max(1.0, 0.0002 * abs(m)):
                tag = "D1"
            if d2 is not None and abs(m - d2) <= max(1.0, 0.0002 * abs(m)):
                tag = "D2"
            if o and not tag and d1 is not None:
                tag = "?"
        f = lambda x: f"{x:14,.1f}" if isinstance(x, (int, float)) else f"{'-':>14}"
        print(f"{r['quarter']:8} {f(m)} {str(r['master_source'] or '-')[:10]:<10} {f(d1)} {f(sa)[2:]:>12} {f(d2)} {f(o.get('재보험계약부채'))[4:]:>10} {f(r.get('summary_책임준비금_일반계정'))[0:16]:>16}  {tag}  [{r.get('own_table_kind', '')}]")


if __name__ == "__main__":
    main()
