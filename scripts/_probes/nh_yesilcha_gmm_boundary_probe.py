"""Investigation probe for inbox/parser/
20260828T1400Z__orchestrator__KR0032__yesilcha_via_gmm_rollforward_total_column.md
(NH농협손해보험 KR0032 원수 예실차, item6).

Re-derives, independently of the ticket's own by-hand arithmetic, across every quarter
the source note format exists (2023.4Q-2026.2Q, 11 filings -- 2023.1-3Q predate the (3)
GMM-only rollforward note and are skipped, not guessed):

  1. The population identity: (3) rollforward's GMM-only 보험수익 (합계 col) ==
     note (8) 보험영업이익 내역's 보험수익 소계 minus its 보험료배분접근법 보험수익 row.
  2. Both loss-component-boundary candidates for item6 (원수 예실차):
       varA = 예상 보험금 − (3)'s 발생보험금 행 합계 (loss-component column INCLUDED)
       varB = 예상 보험금 − (3)'s 발생보험금 행 [손실요소외+발생사고부채] (LC column EXCLUDED)
  3. The identity check that settles the boundary: does note(8)'s own '손실요소배분' row
     (disclosed as a peer line on BOTH revenue and cost sides, never nested inside either
     예상 or 발생 보험금) exactly equal the (3) rollforward's LC-column entry for the same
     row? If yes, every quarter, that is population-wide proof the two are the same
     transaction, and note(8) already keeps 예상 보험금 clean of it -- so item6 must use
     varB (exclude LC), not varA.

Verified result (2026-08-28): population check TRUE in all 11/11 quarters; the
손실요소배분/LC-column identity holds EXACTLY in 10/11 quarters and within KRW 1mm
(rounding) in the 11th (2025.2Q). See extract_tier2_nh / _nh_gmm_incurred4 in
scripts/pl_breakdown/companies.py for the resulting handler code and full citation
of the corroborating evidence (extract_tier2_aia precedent, IFRS17 loss-component
mechanics).

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
     scripts/_probes/nh_yesilcha_gmm_boundary_probe.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.ifrs17.csm_extractor import _iter_tables_with_context
from scripts.pl_breakdown.common import _norm, _row_nums
from scripts.pl_breakdown.tier1 import _ytd_col
from scripts.build_net_income_breakdown import to_num

QUARTERS = [
    ("2023.4Q", REPO / "data/dart/FY2023_Q4/raw/KR0032_NH농협손해보험_20240329001662/20240329001662.xml"),
    ("2024.1Q", REPO / "data/dart/FY2024_Q1/raw/KR0032_NH농협손해보험/20240514001436.xml"),
    ("2024.2Q", REPO / "data/dart/FY2024_Q2/raw/KR0032_NH농협손해보험/20240814001448.xml"),
    ("2024.3Q", REPO / "data/dart/FY2024_Q3/raw/KR0032_NH농협손해보험/20241114001354.xml"),
    ("2024.4Q", REPO / "data/dart/FY2024_Q4/raw/KR0032_NH농협손해보험_20250331003247/20250331003247.xml"),
    ("2025.1Q", REPO / "data/dart/FY2025_Q1/raw/KR0032_NH농협손해보험/20250515001078.xml"),
    ("2025.2Q", REPO / "data/dart/FY2025_Q2/raw/KR0032_NH농협손해보험/20250814001701.xml"),
    ("2025.3Q", REPO / "data/dart/FY2025_Q3/raw/KR0032_NH농협손해보험/20251114001790.xml"),
    ("2025.4Q", REPO / "data/dart/FY2025_Q4/raw/KR0032_NH농협손해보험_20260331004099/20260331004099.xml"),
    ("2026.1Q", REPO / "data/dart/FY2026_Q1/raw/KR0032_NH농협손해보험/20260529001870.xml"),
    ("2026.2Q", REPO / "data/dart/FY2026_Q2/raw/KR0032_NH농협손해보험/20260814003298.xml"),
]


def find_note8(tables):
    for t in tables:
        labs = " ".join(_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows)
        if ("보험영업이익" in (t.caption or "")) and "보험계약마진 상각" in labs \
                and "보험료배분접근법 보험수익" in labs:
            return t
    return None


def find_note3(tables):
    """GMM-only (장기손해보험) rollforward -- (3) note, NOT the reinsurance mirror (5)."""
    for t in tables:
        cap = (t.caption or "").replace(" ", "").replace("\n", "")
        if "보험료배분접근법을적용하지않는보험계약" not in cap or "장기손해보험" not in cap:
            continue
        if not any(_norm(r[0]) == "발생보험금 및 기타보험서비스비용" for r in t.rows):
            continue
        return t   # first table under the caption = 당(반/분)기, not the 전기 comparative
    return None


def _lab01(r):
    """Concatenated label across the (up to 2) leading label columns -- note 8's
    section-header column (rowspan) only appears in the FIRST row of its block, so
    that row's real item label sits in r[1], not r[0]. r[1] is only folded in when it
    is NOT itself a numeric cell (matches extract_tier2_nh's own lab0+lab1 pattern)."""
    lab0 = _norm(r[0])
    if len(r) > 1:
        c1 = _norm(r[1])
        if c1 and to_num(c1) is None:
            return (lab0 + c1).replace(" ", "")
    return lab0.replace(" ", "")


def row(t, label):
    target = label.replace(" ", "")
    for r in t.rows:
        if target in _lab01(r):
            return r
    return None


def main():
    print(f"{'quarter':8s}  {'exp4':>10s} {'inc_incl_LC':>12s} {'inc_excl_LC':>12s}  "
          f"{'varA(incl)':>11s} {'varB(excl)':>11s}  "
          f"{'n8_LCr':>8s} {'n8_LCc':>8s} {'n3_LCcol':>9s}  {'popOK':>6s}")
    for q, path in QUARTERS:
        if not path.exists():
            print(f"{q:8s}  FILE MISSING: {path}")
            continue
        tables = list(_iter_tables_with_context(path))
        n8, n3 = find_note8(tables), find_note3(tables)
        if n8 is None or n3 is None:
            print(f"{q:8s} note8={'Y' if n8 else 'N'} note3={'Y' if n3 else 'N'}  -- skip")
            continue
        col8 = _ytd_col(n8)

        def v8(label):
            r = row(n8, label)
            ns = _row_nums(r) if r is not None else []
            return (ns[col8] if len(ns) > col8 else ns[0]) if ns else None

        exp4 = v8("예상 보험금 및 기타서비스비용")
        n8_lc_rev = v8("손실요소배분")
        lc_rows = [r for r in n8.rows if _norm(r[0]) == "손실요소배분"]
        n8_lc_cost = None
        if len(lc_rows) >= 2:
            ns = _row_nums(lc_rows[1])
            n8_lc_cost = ns[col8] if len(ns) > col8 else (ns[0] if ns else None)
        paa_rev = v8("보험료배분접근법 보험수익")
        rev_subtotal_rows = [r for r in n8.rows if _norm(r[0]) == "소계"]
        n8_rev_subtotal = None
        if rev_subtotal_rows:
            ns = _row_nums(rev_subtotal_rows[0])
            n8_rev_subtotal = ns[col8] if len(ns) > col8 else (ns[0] if ns else None)

        # note 3 GMM rollforward row: [손실요소외, 손실요소, 소계, 발생사고부채, 합계]
        n3_rev_row = row(n3, "보험수익")
        n3_inc_row = row(n3, "발생보험금 및 기타보험서비스비용")
        n3_rev_total = _row_nums(n3_rev_row)[-1] if n3_rev_row is not None else None
        inc_incl_lc = inc_excl_lc = n3_lc_col = None
        if n3_inc_row is not None:
            ns = _row_nums(n3_inc_row)
            if len(ns) >= 5:
                excl_lc, lc, _sub, lic, total = ns[:5]
                n3_lc_col = lc
                inc_incl_lc = total                 # candidate A: row's own 합계 (LC included)
                inc_excl_lc = excl_lc + lic          # candidate B: drop the 손실요소 column

        varA = (exp4 - inc_incl_lc) if None not in (exp4, inc_incl_lc) else None
        varB = (exp4 - inc_excl_lc) if None not in (exp4, inc_excl_lc) else None

        pop_ok = None
        if None not in (n8_rev_subtotal, paa_rev, n3_rev_total):
            pop_ok = abs((n8_rev_subtotal - paa_rev) - abs(n3_rev_total)) < 2  # rounding tol

        def f(x):
            return f"{x:,.0f}" if x is not None else "None"

        print(f"{q:8s}  {f(exp4):>10s} {f(inc_incl_lc):>12s} {f(inc_excl_lc):>12s}  "
              f"{f(varA):>11s} {f(varB):>11s}  "
              f"{f(n8_lc_rev):>8s} {f(n8_lc_cost):>8s} {f(n3_lc_col):>9s}  {str(pop_ok):>6s}")


if __name__ == "__main__":
    main()
