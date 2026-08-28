"""Investigation probe for inbox/parser/
20260828T1900Z__orchestrator__KR0032__reinsurance_yesilcha_item11.md
(NH농협손해보험 KR0032 재보험 예실차, item11).

Mirrors scripts/_probes/nh_yesilcha_gmm_boundary_probe.py (item6, 원수) but for the
reinsurance leg.  Re-derives, independently across every quarter the (5) reinsurance
rollforward note exists, three things:

  1. THE REQUIRED CROSS-CHECK (ticket point 1): does note8 (보험영업이익 내역)'s
     '손실회수요소배분' row (a peer line shown separately on BOTH 재보험수익 and 재보험비용
     sections) match the (5) rollforward's LC ('손실회수요소') column entry for the
     '발생재보험금 및 기타재보험수익' row?  This is the SAME identity check that settled
     item6's boundary (there: '손실요소배분' vs note3's LC column, 10/11 exact).  Do NOT
     assume the answer is the same just because the table structure is symmetric --
     verify it.
  2. The population identity (ticket point 3): note8's 재보험비용 소계 minus its
     보험료배분접근법 재보험서비스비용 row == the (5) rollforward's '재보험서비스비용' row
     (population match, proves 예상재보험비용 is GMM-population-scoped).
  3. Both LC-boundary candidates for the incurred-recovery figure:
       inc_inclLC = (5) row's own 합계 (loss-recovery-component column INCLUDED)
       inc_exclLC = (5) row's [손실회수요소외 + 발생사고자산(부채)] (LC column EXCLUDED)

Sign note: item8 (생명장기 재보험손익) = jang_rerev(재보험수익 소계) - jang_recost(재보험비용
소계) [build_pl_breakdown.py assemble()].  exp4_re ('예상재보험비용') sits inside the
재보험비용 section -- the SUBTRACTED role (same role recsm/rera already occupy, which is
why item9/item10 are stored NEGATED: out[9]=-abs(recsm)).  inc_re ('발생재보험금 및 기타
재보험수익') sits, in the (5) rollforver's OWN row hierarchy, nested under the '재보험수익'
parent row -- the ADDED role (matching jang_rerev's role, mirroring how note3's '발생보험금'
row was nested under 보험서비스비용/jang_cost's role for item6).  So the correct formula is
NOT a literal copy of item6's (예상 - 발생) order -- it is (rev-role term) - (cost-role
term) applied with EACH term's own role, which for reinsurance works out to
inc_re - exp4_re (발생 - 예상, reversed from item6).  This script prints both candidate
signs; the handler code carries the full citation for why the reversed sign was chosen.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
     scripts/_probes/nh_yesilcha_reinsurance_boundary_probe.py
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
    ("2023.1Q", REPO / "data/dart/FY2023_Q1/raw/KR0032_NH농협손해보험/20230515002460.xml"),
    ("2023.2Q", REPO / "data/dart/FY2023_Q2/raw/KR0032_NH농협손해보험/20230814001056.xml"),
    ("2023.3Q", REPO / "data/dart/FY2023_Q3/raw/KR0032_NH농협손해보험/20231114000995.xml"),
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


def find_note5(tables):
    """GMM-only (장기비례재보험) rollforward -- the (5) note, mirror of note3's (3)."""
    for t in tables:
        cap = (t.caption or "").replace(" ", "").replace("\n", "")
        if "보험료배분접근법을적용하지않는재보험계약" not in cap or "장기비례재보험" not in cap:
            continue
        if not any(_norm(r[0]) == "발생재보험금 및 기타재보험수익" for r in t.rows):
            continue
        return t   # first table under the caption = 당(반/분)기, not the 전기 comparative
    return None


def _lab01(r):
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


SEC = {"보험수익": "보험수익", "보험서비스비용": "보험서비스비용",
       "재보험수익": "재보험수익", "재보험비용": "재보험비용",
       "재보험서비스비용": "재보험비용"}


def section_values(n8, col8):
    """Section-aware walk of note8 -- deliberately mirrors extract_tier2_nh's OWN production
    logic verbatim (lab = (lab0+' '+lab1) stripped of spaces, substring-matched), not a
    reimplementation, since that logic is already proven correct in the live handler.  A
    section-header column via rowspan only appears in the FIRST row of its block, which is
    why lab always concatenates both cells and callers match by substring rather than
    equality (the row's own first data value ends up harmlessly appended for non-first rows,
    e.g. '위험조정변동3,822' -- substring '위험조정변동' still matches)."""
    section = None
    vals = {}       # section -> [(concat_label, value), ...] in document order
    subtotal = {}   # section -> value of its OWN (first) '소계' row
    for r in n8.rows:
        lab0 = _norm(r[0])
        lab1 = _norm(r[1]) if len(r) > 1 else ""
        if lab0 in SEC:
            section = SEC[lab0]
        lab = (lab0 + " " + lab1).replace(" ", "")
        ns = _row_nums(r)
        v = (ns[col8] if len(ns) > col8 else ns[0]) if ns else None
        if v is None or section is None:
            continue
        if lab0 == "소계":
            subtotal.setdefault(section, v)   # FIRST 소계 per section (mirrors extract_tier2_nh's
            continue                           # own subtotal() which returns on first match)
        vals.setdefault(section, []).append((lab, v))
    return vals, subtotal


def main():
    print(f"{'quarter':8s}  {'exp4_re':>9s} {'inc_inclLC':>11s} {'inc_exclLC':>11s}  "
          f"{'item11=inc-exp(excl)':>20s} {'naive=exp-inc(excl)':>20s}  "
          f"{'n8_LCr':>8s} {'n8_LCc':>8s} {'n5_LCcol':>9s} {'LCok':>5s}  {'popOK':>6s}")
    for q, path in QUARTERS:
        if not path.exists():
            print(f"{q:8s}  FILE MISSING: {path}")
            continue
        tables = list(_iter_tables_with_context(path))
        n8, n5 = find_note8(tables), find_note5(tables)
        if n8 is None or n5 is None:
            print(f"{q:8s} note8={'Y' if n8 else 'N'} note5={'Y' if n5 else 'N'}  -- skip")
            continue
        col8 = _ytd_col(n8)
        vals, subtotal = section_values(n8, col8)

        def first(sec, needle):
            for lab, v in vals.get(sec, []):
                if needle in lab:
                    return v
            return None

        exp4_re = first("재보험비용", "예상재보험비용")
        n8_lc_rev = first("재보험수익", "손실회수요소배분")   # 발생 side (재보험수익 section)
        n8_lc_cost = first("재보험비용", "손실회수요소배분")  # 예상 side (재보험비용 section)
        paa_recost = first("재보험비용", "보험료배분접근법재보험서비스비용")
        n8_recost_subtotal = subtotal.get("재보험비용")

        # (5) rollforward row: [손실회수요소외, 손실회수요소, 소계, 발생사고자산(부채), 합계]
        # NOTE: _row_nums() SKIPS '-' cells (to_num('-') is None), which shifts column
        # positions whenever 손실회수요소외 (very often '-'/nil) is blank -- must index the
        # fixed 5-cell layout directly (r[1:6]) with '-' read as 0.0, not via _row_nums.
        def cell0(x):
            v = to_num(x)
            return v if v is not None else 0.0

        n5_svccost_row = row(n5, "재보험서비스비용")
        n5_inc_row = row(n5, "발생재보험금 및 기타재보험수익")
        n5_svccost_total = _row_nums(n5_svccost_row)[-1] if n5_svccost_row is not None else None
        inc_incl_lc = inc_excl_lc = n5_lc_col = None
        if n5_inc_row is not None and len(n5_inc_row) >= 6:
            excl_lc, lc, _sub, incurred_asset, total = (cell0(c) for c in n5_inc_row[1:6])
            n5_lc_col = lc
            inc_incl_lc = total                       # candidate incl LC (row's own 합계)
            inc_excl_lc = excl_lc + incurred_asset     # candidate excl LC

        item11 = (inc_excl_lc - exp4_re) if None not in (inc_excl_lc, exp4_re) else None
        naive = (exp4_re - inc_excl_lc) if None not in (inc_excl_lc, exp4_re) else None

        lc_ok = None
        if None not in (n8_lc_rev, n8_lc_cost, n5_lc_col):
            lc_ok = abs(n8_lc_rev - n8_lc_cost) < 2 and abs(n8_lc_rev - n5_lc_col) < 2

        pop_ok = None
        if None not in (n8_recost_subtotal, paa_recost, n5_svccost_total):
            pop_ok = abs((n8_recost_subtotal - paa_recost) - abs(n5_svccost_total)) < 2

        def f(x):
            return f"{x:,.0f}" if x is not None else "None"

        print(f"{q:8s}  {f(exp4_re):>9s} {f(inc_incl_lc):>11s} {f(inc_excl_lc):>11s}  "
              f"{f(item11):>20s} {f(naive):>20s}  "
              f"{f(n8_lc_rev):>8s} {f(n8_lc_cost):>8s} {f(n5_lc_col):>9s} {str(lc_ok):>5s}  {str(pop_ok):>6s}")


if __name__ == "__main__":
    main()
