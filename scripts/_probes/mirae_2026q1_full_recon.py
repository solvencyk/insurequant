"""KR0079 2026.1Q -- FULL fresh reconciliation (coordinator follow-up to inbox/parser/
20260829T1600Z: scope now widened to include this quarter). Mirrors
mirae_2025q2q3_full_recon.py's method exactly but recomputed independently for THIS quarter --
per-product [손실요소외,손실요소,LIC] split (candidate A vs B), boundary rule (표3 손실요소열
합 vs 표2 손실요소배분액 합), population checks A/B. Read-only, no master touched.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _iter_tables_by_basis, _row_nums  # noqa: E402
from scripts.pl_breakdown.companies import (  # noqa: E402
    _MA_ACT4_ROW, _MA_EXP4_ROW_VARIANTS, _MA_7COMP_ROWS,
    _ma_find_product_table, _ma_row_sum, _ma_tier1_ins_rev, _ma_yesilcha_direct,
)
from scripts.pl_breakdown.tier1 import _header_blob  # noqa: E402

XML_PATH = ROOT / "data/dart/FY2026_Q1/raw/KR0079_미래에셋생명/20260529001897.xml"

print(f"=== 2026.1Q: {XML_PATH} ===")
tables = list(_tag_basis(
    list(_iter_tables_by_basis(XML_PATH, _iter_tables_with_context)), XML_PATH))
ofs_tables = _prefer_ofs(tables)
print(f"total tables={len(tables)}  ofs tables={len(ofs_tables)}")

t_exp = _ma_find_product_table(ofs_tables, _MA_EXP4_ROW_VARIANTS)
t_act = _ma_find_product_table(ofs_tables, _MA_ACT4_ROW)
print(f"t_exp line={t_exp.line_no if t_exp else None} caption={t_exp.caption if t_exp else None!r}")
print(f"t_act line={t_act.line_no if t_act else None} caption={t_act.caption if t_act else None!r}")
if t_exp is None or t_act is None:
    print("ABSTAIN: table missing")
    raise SystemExit(0)

# raw row dump for t_act (candidate A needs the per-product [외,손실요소,LIC] split)
act_nums = None
for r in t_act.rows:
    if _MA_ACT4_ROW in "".join(r[:2]):
        print(f"\nraw ACT row cells: {r}")
        act_nums = _row_nums(r)
        print(f"raw ACT numeric cells ({len(act_nums)}): {act_nums}")
        break
if act_nums is None:
    print("ACT row not found in t_act despite table match -- ABSTAIN")
    raise SystemExit(0)

if len(act_nums) % 3 != 0:
    print(f"WARNING: {len(act_nums)} not divisible by 3 -- cannot split into "
          f"[손실요소외,손실요소,LIC] triplets, skipping candidate-A analysis")
else:
    n_products = len(act_nums) // 3
    loss_ext = act_nums[0::3]
    loss_elem = act_nums[1::3]
    lic = act_nums[2::3]
    print(f"\nper-product split ({n_products} products):")
    print(f"  손실요소외: {loss_ext}  (all zero: {all(v == 0 for v in loss_ext)})")
    print(f"  손실요소  : {loss_elem}  sum={sum(loss_elem):,.0f}")
    print(f"  LIC       : {lic}  sum={sum(lic):,.0f}")
    cand_a = sum(lic)
    print(f"  candidate A (LIC-only) = {cand_a:,.0f}")

exp = _ma_row_sum(t_exp, _MA_EXP4_ROW_VARIANTS)
loss_alloc = _ma_row_sum(t_exp, "손실요소배분액")
full_row = _ma_row_sum(t_act, _MA_ACT4_ROW)
print(f"\nexp(예상4종)={exp:,.0f}  full_row(발생4종 all-cols)={full_row:,.0f}  "
      f"loss_alloc(표2 손실요소배분액)={loss_alloc:,.0f}")
cand_b = full_row - loss_alloc
print(f"candidate B (full_row - loss_alloc) = {cand_b:,.0f}")
if len(act_nums) % 3 == 0:
    print(f"A - B = {cand_a - cand_b:,.6f}  "
          f"({'IDENTICAL' if abs(cand_a - cand_b) < 0.5 else 'DIFFER -- use candidate B'})")
    act_loss_elem_sum = sum(loss_elem)
    print(f"\nboundary check: 표3 손실요소열 합={act_loss_elem_sum:,.0f}  vs  "
          f"표2 손실요소배분액행 합={loss_alloc:,.0f}  "
          f"-> {'MATCH' if abs(act_loss_elem_sum - loss_alloc) < 0.5 else 'MISMATCH'} "
          f"(diff={act_loss_elem_sum - loss_alloc:,.6f})")

item6 = (exp - cand_b) / 1e6
print(f"\nitem6 (candidate B / NH formula) = {item6:,.6f} 백만원")

total7 = sum(v for v in (_ma_row_sum(t_exp, c) for c in _MA_7COMP_ROWS) if v is not None)
rev_lump = _ma_row_sum(t_act, "보험수익")
check_a = rev_lump is not None and abs(abs(total7) - abs(rev_lump)) < 1.0
print(f"\ncheck A (internal, 표2 7성분 합 vs 표3 보험수익 lump): total7={total7:,.0f} "
      f"rev_lump={rev_lump:,.0f}  diff={total7 + rev_lump:,.6f}  -> {check_a}")

anchor = _ma_tier1_ins_rev(ofs_tables)
check_b = anchor is not None and abs(abs(total7) - abs(anchor)) < 1.0
print(f"check B (Tier-1 anchor, 별도 일반보험서비스수익): anchor={anchor}  "
      f"diff={(total7 - anchor) if anchor else None}  -> {check_b}")

print(f"\nGATE: {'PASS' if (check_a and check_b) else 'FAIL -> abstain'}")

prod_item6 = _ma_yesilcha_direct(tables)
print(f"\nPRODUCTION _ma_yesilcha_direct(tables) = {prod_item6}")
