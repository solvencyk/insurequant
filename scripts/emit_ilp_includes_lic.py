# -*- coding: utf-8 -*-
"""
P4 (ticket 20261010T0945Z lic_load_stage1): sidecar data/_derived/ilp_includes_lic.json = the companies whose
경영공시 2-4 total (insurance_liability_portfolio.json item 8) ALREADY CONTAINS the 발생사고요소(LIC), although
the 2-4 footnote says the table was prepared for the 잔여보장요소 only.  The designer uses it to tell the reader
that the left bar of these companies is LRC+LIC.  Master cells are NOT changed.

Criterion (derived, not hand-picked): in ALL six quarters 2025.1Q~2026.2Q
  |item 8 - item 15| <= max(5억, 0.01 % of item 15)         (item 15 = DART LRC+LIC, 부채 기준; items are 억원)
  and item 8 differs from item 14 (DART LRC only) by more than 1 %  (so it cannot be an LRC-only number),
  and |item 8 x100 / IFRS17_BS item 20 - 1| <= 0.01 %.
Spot check for ABL (KR0070) 2026.2Q: the DART 측정요소별 변동표 closing row (별도, 당반기: T667/T669/T671/T673 of
20260814003770.xml) sums to BEL 15,929,245 / RA 306,588 / CSM 1,070,412 백만원 -- the same as the 2-4 table's
(item 1+4, 2+5, 3+6) x100 within rounding, i.e. 2-4 carries the whole BEL/RA/CSM, not only the LRC part.

Usage:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/emit_ilp_includes_lic.py [--write]
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import extract_insurance_liability_lic as X          # noqa: E402  (table readers only)

ILP = REPO / "insurance_liability_portfolio.json"
BS = REPO / "IFRS17_BS.json"
PROV = REPO / "insurance_liability_portfolio_provenance.json"
OUT = REPO / "data" / "_derived" / "ilp_includes_lic.json"
QUARTERS = ["2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"]
# 2026-10-10 backfill (ticket 20261010T1600Z): the company set is still decided on the six stage-1 quarters; the year-end
# points loaded before 2025 are then tested cell by cell for the companies in that set (a cell that fails is reported, the
# company is NOT dropped).  Extend this list when another pre-2025 quarter is loaded.
EXTRA_QUARTERS = ["2023.4Q", "2024.4Q"]


def abl_spot_check():
    """closing BEL/RA/CSM of the four 당반기 measurement tables of ABL 2026.2Q (별도) vs the 2-4 items"""
    paths = glob.glob(str(REPO / "data/dart/FY2026_Q2/raw/KR0070_*/*.xml"))
    if not paths:
        return None
    txt = X.read_xml(paths[0])
    want = {667, 669, 671, 673}
    bel = ra = csm = 0.0
    seen = set()
    for i, m in enumerate(X.TAB_RE.finditer(txt)):
        if i not in want:
            continue
        g, _ = X.parse_table(m.group(0))
        for r in g:
            lab = X.row_label(r, 1)
            if "반기말" in lab and "보험계약순부채" in lab:
                v = [X.parse_num(c) for c in r[1:5]]
                if None in v:
                    return None
                bel, ra, csm = bel + v[0], ra + v[1], csm + v[2]
                seen.add(i)
                break
    if seen != want:
        return None
    return {"file": "data/dart/FY2026_Q2/raw/KR0070_에이비엘생명보험/20260814003770.xml", "tables": sorted(want),
            "bel_mm": bel, "ra_mm": ra, "csm_mm": csm}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    ilp = json.load(open(ILP, encoding="utf-8"))
    bs = json.load(open(BS, encoding="utf-8"))
    prov = json.load(open(PROV, encoding="utf-8"))
    v = {}
    names = {}
    for r in ilp:
        v.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]
        names[r["원보험사코드"]] = r["원수사명"]
    b20 = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in bs if r["항목번호"] == 20}
    codes = sorted(names)
    chosen, cells = [], []
    for c in codes:
        rows = []
        ok_all = True
        for q in QUARTERS:
            d = v.get((c, q), {})
            i8, i14, i15, i10 = d.get(8), d.get(14), d.get(15), d.get(10)
            b = b20.get((c, q))
            if None in (i8, i14, i15, i10) or b is None:
                ok_all = False
                break
            c1 = abs(i8 - i15) <= max(5.0, 1e-4 * abs(i15))
            c2 = abs(i8 - i14) > 0.01 * abs(i14)
            c3 = abs(i8 * 100.0 / b - 1) <= 1e-4
            if not (c1 and c2 and c3):
                ok_all = False
                break
            rows.append({"company_code": c, "quarter": q, "item8_eok": i8, "item15_eok": i15, "item14_eok": i14, "item10_eok": i10,
                         "bs20_eok": round(b / 100.0, 2),
                         "item8_vs_bs20_pct": round((i8 * 100.0 / b - 1) * 100, 5),
                         "item8_vs_item15_pct": round((i8 / i15 - 1) * 100, 5),
                         "lic_share_of_item8_pct": round(i10 / i8 * 100, 2)})
        if ok_all and len(rows) == len(QUARTERS):
            chosen.append(c)
            cells += rows
    # pre-2025 year-end points: same three tests, cell by cell, for the companies already chosen
    extra_q = {c: [] for c in chosen}
    extra_not = []
    for c in chosen:
        for q in EXTRA_QUARTERS:
            d = v.get((c, q), {})
            i8, i14, i15, i10 = d.get(8), d.get(14), d.get(15), d.get(10)
            b = b20.get((c, q))
            if None in (i8, i14, i15, i10) or b is None:
                if any(n in d for n in (1, 8, 10, 14, 15)):
                    extra_not.append({"company_code": c, "quarter": q, "why": "items missing (8/10/14/15) or no BS item 20"})
                continue          # quarter not loaded at all: nothing to test
            c1 = abs(i8 - i15) <= max(5.0, 1e-4 * abs(i15))
            c2 = abs(i8 - i14) > 0.01 * abs(i14)
            c3 = abs(i8 * 100.0 / b - 1) <= 1e-4
            if c1 and c2 and c3:
                extra_q[c].append(q)
                cells.append({"company_code": c, "quarter": q, "item8_eok": i8, "item15_eok": i15, "item14_eok": i14, "item10_eok": i10,
                              "bs20_eok": round(b / 100.0, 2),
                              "item8_vs_bs20_pct": round((i8 * 100.0 / b - 1) * 100, 5),
                              "item8_vs_item15_pct": round((i8 / i15 - 1) * 100, 5),
                              "lic_share_of_item8_pct": round(i10 / i8 * 100, 2)})
            else:
                extra_not.append({"company_code": c, "quarter": q, "why": f"criterion fails: c1={c1} c2={c2} c3={c3}"})
    print("companies whose 2-4 total contains the LIC:", [(c, names[c]) for c in chosen])
    if extra_not:
        print("extra quarters NOT included:", extra_not)
    for r in cells:
        print(f"  {r['company_code']} {r['quarter']}: item8 {r['item8_eok']:,.1f} item15 {r['item15_eok']:,.2f} LRC-only {r['item14_eok']:,.2f} "
              f"| vs BS20 {r['item8_vs_bs20_pct']:+.5f}% | vs item15 {r['item8_vs_item15_pct']:+.5f}% | LIC share {r['lic_share_of_item8_pct']}%")
    spot = abl_spot_check()
    spot_rec = None
    if spot:
        d = v[("KR0070", "2026.2Q")]
        two4 = {"bel": (d[1] + d[4]) * 100.0, "ra": (d[2] + d[5]) * 100.0, "csm": (d[3] + d[6]) * 100.0}
        spot_rec = {**spot, "two_four_x100_mm": two4,
                    "diff_mm": {"bel": spot["bel_mm"] - two4["bel"], "ra": spot["ra_mm"] - two4["ra"], "csm": spot["csm_mm"] - two4["csm"]},
                    "reading": "DART 측정요소별 합계 == 2-4 (item 1+4, 2+5, 3+6) x100 within 억원 rounding (<= 100 백만원 each) => 2-4 holds the whole BEL/RA/CSM"}
        print("ABL 2026.2Q spot check:", json.dumps(spot_rec, ensure_ascii=False))
    out = {
        "name": "ilp_includes_lic", "generated_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"),
        "emitted_by": "scripts/emit_ilp_includes_lic.py",
        "meaning": ("insurance_liability_portfolio.json item 8 (보험부채_합계, 경영공시 2-4) of these companies already contains the 발생사고요소(LIC) "
                    "although the 2-4 footnote says it was prepared for the 잔여보장요소 only. For them item 8 ~ item 15 (LRC+LIC) ~ IFRS17_BS item 20. "
                    "Master cells are not changed; the designer shows a notice on the left bar."),
        "criterion": ("all 6 quarters 2025.1Q~2026.2Q: |item8-item15| <= max(5억, 0.01%) and |item8-item14| > 1% and |item8*100/BS20-1| <= 0.01%; "
                      "the pre-2025 year-end points (EXTRA_QUARTERS) are added per cell when the same three tests pass"),
        "companies": {c: {"원수사명": names[c], "quarters": sorted(extra_q[c]) + QUARTERS} for c in chosen},
        "cells": sorted(cells, key=lambda x: (x["company_code"], x["quarter"])), "spot_checks": [spot_rec] if spot_rec else [],
        "extra_quarters_not_included": extra_not,
    }
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print("wrote", OUT.relative_to(REPO))
    else:
        print("dry run (use --write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
