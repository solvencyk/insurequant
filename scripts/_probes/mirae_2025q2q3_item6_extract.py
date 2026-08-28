"""KR0079 (미래에셋생명) item6 extraction dry-run for 2025.2Q / 2025.3Q -- orchestrator ticket
inbox/parser/20260829T1600Z (glob-blindspot correction: xml IS present under xml/<rcept>.xml
for both quarters, prior survey's "raw is zip-only" call was wrong).

Mirrors scripts/_probes/mirae_item6_extract_test.py's method (same production helpers from
scripts/pl_breakdown/companies.py, not reimplemented), but for THESE two quarters specifically:
  - dumps the raw ACT-row cells (not just a sum) so the LRC_손실요소외/손실요소/LIC column
    split can be read directly instead of assumed from the 2026.2Q layout
  - reports candidate A (LIC-column-only sum) AND candidate B (NH-style: full row sum minus
    손실요소배분액) separately, plus the diff between them
  - reports the boundary-rule cross-check (표3 손실요소열 합 vs 표2 손실요소배분액행 합)
    independently per quarter
  - runs the actual production _ma_yesilcha_direct() so the reported item6 is exactly what
    the real handler would emit, not a hand-rolled number
Read-only: does not touch any master JSON.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import (  # noqa: E402
    _tag_basis, _prefer_ofs, _iter_tables_by_basis, _row_nums,
)
from scripts.pl_breakdown.companies import (  # noqa: E402
    _MA_EXP4_ROW, _MA_ACT4_ROW, _MA_7COMP_ROWS,
    _ma_find_product_table, _ma_row_sum, _ma_tier1_ins_rev, _ma_yesilcha_direct,
)

QUARTERS = [
    ("2025.2Q", ROOT / "data/dart/FY2025_Q2/raw/KR0079_미래에셋생명/xml/20250814003532.xml"),
    ("2025.3Q", ROOT / "data/dart/FY2025_Q3/raw/KR0079_미래에셋생명/xml/20251114002791.xml"),
]


def dump_row(t, needle, label):
    for r in t.rows:
        if needle in "".join(r[:2]):
            print(f"    raw {label} row cells: {r}")
            nums = _row_nums(r)
            print(f"    raw {label} numeric cells ({len(nums)}): {nums}")
            return nums
    print(f"    {label} row NOT FOUND")
    return None


def try_quarter(label, xml_path):
    print(f"\n{'=' * 70}\n=== {label}: {xml_path} ===")
    if not xml_path.exists():
        print("  [xml not on disk]")
        return
    tables = list(_tag_basis(
        list(_iter_tables_by_basis(xml_path, _iter_tables_with_context)), xml_path))
    ofs_tables = _prefer_ofs(tables)
    print(f"  total tables={len(tables)}  ofs tables={len(ofs_tables)}")

    t_exp = _ma_find_product_table(ofs_tables, _MA_EXP4_ROW)
    t_act = _ma_find_product_table(ofs_tables, _MA_ACT4_ROW)
    print(f"  t_exp found: {t_exp is not None}"
          f"{'  caption=' + repr(t_exp.caption) + ' line=' + str(t_exp.line_no) if t_exp else ''}")
    print(f"  t_act found: {t_act is not None}"
          f"{'  caption=' + repr(t_act.caption) + ' line=' + str(t_act.line_no) if t_act else ''}")
    if t_exp is None or t_act is None:
        print("  GATE: table not found -> abstain (matches try_quarter probe behaviour)")
        return

    print(f"  t_act.header={t_act.header}")

    # ---- raw row dump for direct column inspection (candidate A needs LIC column) ----
    act_nums = dump_row(t_act, _MA_ACT4_ROW, "ACT (발생 4종)")
    exp_nums_row = dump_row(t_exp, _MA_EXP4_ROW, "EXP (예상 4종)")
    loss_alloc_row = dump_row(t_exp, "손실요소배분액", "손실요소배분액")

    if act_nums is None:
        print("  GATE: ACT row missing -> abstain")
        return
    if len(act_nums) % 3 != 0:
        print(f"  WARNING: act_nums length {len(act_nums)} not divisible by 3 -- "
              f"cannot assume [손실요소외,손실요소,LIC] triplet layout, skipping candidate-A split")
    else:
        n_products = len(act_nums) // 3
        loss_ext = act_nums[0::3]     # 손실요소외
        loss_elem = act_nums[1::3]    # 손실요소
        lic = act_nums[2::3]          # 발생사고부채(LIC)
        print(f"  per-product split ({n_products} products):")
        print(f"    손실요소외: {loss_ext}  (all zero: {all(v == 0 for v in loss_ext)})")
        print(f"    손실요소  : {loss_elem}  sum={sum(loss_elem):,.0f}")
        print(f"    LIC       : {lic}  sum={sum(lic):,.0f}")
        cand_a = sum(lic)
        print(f"  candidate A (LIC-column-only sum) = {cand_a:,.0f}")

    exp = _ma_row_sum(t_exp, _MA_EXP4_ROW)
    loss_alloc = _ma_row_sum(t_exp, "손실요소배분액")
    full_row = _ma_row_sum(t_act, _MA_ACT4_ROW)
    if exp is None or loss_alloc is None or full_row is None:
        print(f"  row missing (via _ma_row_sum): exp={exp} loss_alloc={loss_alloc} full_row={full_row}")
        return
    cand_b = full_row - loss_alloc
    print(f"  exp(예상4종)={exp:,.0f}  full_row(발생4종 all-cols)={full_row:,.0f}  "
          f"loss_alloc(표2 손실요소배분액)={loss_alloc:,.0f}")
    print(f"  candidate B (full_row - loss_alloc) = {cand_b:,.0f}")
    if len(act_nums) % 3 == 0:
        diff = cand_a - cand_b
        print(f"  candidate A - candidate B = {diff:,.6f}  "
              f"({'IDENTICAL' if abs(diff) < 0.5 else 'DIFFER -- must use candidate B (NH rule)'})")

    # ---- boundary rule: 표3 손실요소열 합 vs 표2 손실요소배분액행 합 ----
    if len(act_nums) % 3 == 0:
        act_loss_elem_sum = sum(loss_elem)
        print(f"  boundary check: 표3 손실요소열 합={act_loss_elem_sum:,.0f}  vs  "
              f"표2 손실요소배분액행 합={loss_alloc:,.0f}  "
              f"-> {'MATCH' if abs(act_loss_elem_sum - loss_alloc) < 0.5 else 'MISMATCH'} "
              f"(diff={act_loss_elem_sum - loss_alloc:,.6f})")

    item6_direct = (exp - cand_b) / 1e6
    print(f"  item6 (NH-formula, exp - candB) = {item6_direct:,.6f} 백만원")

    # ---- population checks (mirrors _ma_yesilcha_direct's internal gates exactly) ----
    total7 = sum(v for v in (_ma_row_sum(t_exp, c) for c in _MA_7COMP_ROWS) if v is not None)
    rev_lump = _ma_row_sum(t_act, "보험수익")
    check_a = rev_lump is not None and abs(abs(total7) - abs(rev_lump)) < 1.0
    print(f"  check A (internal, 표2 7성분 합 vs 표3 보험수익 lump): total7={total7:,.0f} "
          f"rev_lump={rev_lump} -> {check_a}")

    anchor = _ma_tier1_ins_rev(ofs_tables)
    check_b = anchor is not None and abs(abs(total7) - abs(anchor)) < 1.0
    print(f"  check B (Tier-1 anchor, 별도 일반보험서비스수익): anchor={anchor} -> {check_b}")

    print(f"  GATE (internal): {'PASS' if (check_a and check_b) else 'FAIL -> abstain'}")

    # ---- actual production function, end to end ----
    prod_item6 = _ma_yesilcha_direct(tables)
    print(f"  PRODUCTION _ma_yesilcha_direct(tables) = {prod_item6}")


for label, path in QUARTERS:
    try_quarter(label, path)
