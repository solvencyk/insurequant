#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 1: the same KIND of mismatch as KR1098 2026.2Q 자본금 for every company/quarter.

The 4-1 'B/S상 자기자본' table of a management disclosure prints [current quarter, previous quarter, quarter before that]; the 8-1
statement prints [current, prior year-end].  This compares EVERY printed column (the equity table only where the column closes:
자본총계 = sum of its lines) against the master cell of the period the column belongs to, for 자본총계(3) · 기타포괄손익누계액(4) ·
자본금(30) · 이익잉여금(31), all 48 companies.  Observations are read with the same code as Stage B (stage_b.observations) but the unit
is taken from the table caption, so a wrong master total can no longer hide a table.  Read-only.

Output: data/_derived/bspl_followup_20261011/equity_scan.json   (+ printed disagreements)
  --items 30,3  (default 30,3,4,31)   --tol 0.005 (relative)   --company KR1098
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402
from bspl_granularity.views import view_all  # noqa: E402

OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "equity_scan.json"
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
CODES = sorted({p.name.split("_")[0] for p in (ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "tables").glob("KR*.json")})
LINE = {3: "자본총계", 4: "AOCI", 30: "자본금", 31: "이익잉여금"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default="30,3,4,31")
    ap.add_argument("--tol", type=float, default=0.005)
    ap.add_argument("--company", default="")
    a = ap.parse_args()
    items = [int(x) for x in a.items.split(",")]
    all_v, anchor, disc, meta = B.load_master()
    res = []
    codes = a.company.split(",") if a.company else CODES
    for code in codes:
        mv = all_v.get(code, {})
        for q in QS:
            doc = B.load_tables(code, q)
            if not doc:
                continue
            # the tables Stage B itself would read: every equity table + the picked 8-1 (first, and the audit statement when present);
            # other bs_full tables of a filing are IFRS17 transition-effect tables (제1104호 vs 제1117호) and must not be compared
            picked = B.pick_tables(doc, "bs_full")
            bs_tabs = picked[:1] + [t for t in picked[1:] if t.get("src") == "audit"]
            for t in [t for t in doc["tables"] if t["kind"] == "equity"] + bs_tabs:
                if t["kind"] == "bs_full" and t.get("basis") == "연결":
                    continue
                unit = t.get("unit")
                f = B.UNIT_FACTOR.get(unit)
                if f is None:
                    continue
                va = view_all(t)
                ncol = 3 if t["kind"] == "equity" else 2
                for c in range(ncol):
                    ok_col = None
                    if t["kind"] == "equity":
                        ok_col = B.equity_col_ok(t, c)
                        if ok_col is False:
                            continue
                    tq = (q if c == 0 else B.prev_q(q, c)) if t["kind"] == "equity" else (q if c == 0 else B.prev_year_end(q))
                    for it in items:
                        rows = va.get(LINE[it])
                        if not rows:
                            continue
                        from bspl_granularity.stage_b import _cv
                        v = _cv(rows[0], c)
                        if v is None:
                            continue
                        m = mv.get((it, tq))
                        if m is None:
                            res.append({"code": code, "pdf_quarter": q, "quarter": tq, "col": c, "item": it, "kind": t["kind"],
                                        "page": t["page"], "disclosure": v * f, "master": None, "rel": None, "closed": ok_col,
                                        "basis": t.get("basis"), "unit": unit})
                            continue
                        val = v * f
                        den = max(abs(m), 1.0)
                        rel = (val - m) / den
                        tolr = max(B.UNIT_PREC[unit] / den * 2.5, 1e-9)
                        res.append({"code": code, "pdf_quarter": q, "quarter": tq, "col": c, "item": it, "kind": t["kind"], "page": t["page"],
                                    "disclosure": val, "master": m, "rel": rel, "closed": ok_col, "basis": t.get("basis"), "unit": unit,
                                    "within_rounding": abs(val - m) <= max(B.UNIT_PREC[unit] * 2.5, 1.0)})
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    both = [r for r in res if r["master"] is not None]
    bad = [r for r in both if not r["within_rounding"] and abs(r["rel"]) > a.tol]
    print(f"observations {len(res)}; with master value {len(both)}; disagreements > {a.tol:.1%}: {len(bad)}")
    # group identical (code, quarter, item, disclosure) across several filings
    seen = {}
    for r in bad:
        k = (r["code"], r["quarter"], r["item"], round(r["disclosure"], 1))
        seen.setdefault(k, []).append(r)
    for k, lst in sorted(seen.items()):
        r = lst[0]
        srcs = ",".join(sorted({f"{x['pdf_quarter']}c{x['col']}{x['kind'][0]}" for x in lst}))
        print(f"{r['code']} {r['quarter']} item{r['item']} master {r['master']:>16,.2f} disclosure {r['disclosure']:>16,.2f} rel {r['rel']:+.2%} [{srcs}]")


if __name__ == "__main__":
    main()
