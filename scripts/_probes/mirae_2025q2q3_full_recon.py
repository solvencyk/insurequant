"""KR0079 2025.2Q / 2025.3Q -- full manual reconciliation using the ALT label set found by
mirae_2025q2q3_dump_texp_candidate.py (production _MA_EXP4_ROW etc. don't match this quarter's
exact wording, but the 표2 note DOES exist under a paraphrase -- see that probe's output).
Computes: exp (7-comp sum, mixed existing+alt needles), act/loss_alloc/candidates A&B (via
existing _MA_ACT4_ROW, which DOES match), the two population checks (internal + Tier-1 anchor),
the boundary rule, and the resulting item6 -- entirely by direct arithmetic on the same
ExtractedTable objects the production code would see, so this is a preview of what a
label-variant-aware handler would emit, NOT yet wired into companies.py. Read-only.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _iter_tables_by_basis  # noqa: E402
from scripts.pl_breakdown.companies import (  # noqa: E402
    _MA_ACT4_ROW, _ma_find_product_table, _ma_row_sum, _ma_tier1_ins_rev,
)

QUARTERS = [
    ("2025.2Q", ROOT / "data/dart/FY2025_Q2/raw/KR0079_미래에셋생명/xml/20250814003532.xml"),
    ("2025.3Q", ROOT / "data/dart/FY2025_Q3/raw/KR0079_미래에셋생명/xml/20251114002791.xml"),
]

# ALT needles -- rows 2/4/6/7 already match the EXISTING production _MA_7COMP_ROWS needles via
# substring (confirmed in mirae_2025q2q3_dump_texp_candidate.py output), only 1/3/5 need a
# variant string for this quarter's exact wording.
ALT_EXP4_ROW = "발생한 보험금 및 그 밖의 발생한 보험서비스비용에 따른 증가분"
ALT_7COMP_ROWS = (
    ALT_EXP4_ROW,
    "비금융위험에 대한 위험조정의 변동분",                       # unchanged, matches existing
    "서비스의 이전으로 당기손익에 인식한 보험계약마진",             # ALT of "보험계약서비스의 이전..."
    "손실요소배분액",                                          # unchanged, exact match
    "경험조정에 따른 증가분(감소분), 보험계약부채(자산)",           # ALT of "경험 조정을 통한 증가"
    "기타 변동에 의한 증가",                                    # unchanged, matches existing
    "보험취득 현금흐름의 회수와 관련되는 보험료",                   # unchanged, matches existing
)


def find_exp_alt(ofs_tables):
    cands = [t for t in ofs_tables
              if "사망보험" in " ".join(" ".join(h) for h in t.header).replace(" ", "")
              and "건강보험" in " ".join(" ".join(h) for h in t.header).replace(" ", "")
              and any(ALT_EXP4_ROW in "".join(r[:2]) for r in t.rows)]
    cands.sort(key=lambda t: t.line_no)
    return cands[0] if cands else None


def try_quarter(label, xml_path):
    print(f"\n{'=' * 70}\n=== {label} ===")
    tables = list(_tag_basis(
        list(_iter_tables_by_basis(xml_path, _iter_tables_with_context)), xml_path))
    ofs_tables = _prefer_ofs(tables)

    t_exp = find_exp_alt(ofs_tables)
    t_act = _ma_find_product_table(ofs_tables, _MA_ACT4_ROW)
    print(f"  t_exp(alt) line={t_exp.line_no if t_exp else None}  "
          f"t_act line={t_act.line_no if t_act else None}")
    if t_exp is None or t_act is None:
        print("  ABSTAIN: table missing")
        return

    exp = _ma_row_sum(t_exp, ALT_EXP4_ROW)
    loss_alloc = _ma_row_sum(t_exp, "손실요소배분액")
    full_row = _ma_row_sum(t_act, _MA_ACT4_ROW)
    print(f"  exp(예상4종, alt)={exp:,.0f}  full_row(발생4종 all-cols)={full_row:,.0f}  "
          f"loss_alloc(표2 손실요소배분액)={loss_alloc:,.0f}")

    cand_b = full_row - loss_alloc
    print(f"  candidate B (full_row - loss_alloc) = {cand_b:,.0f}")

    # candidate A: LIC-column-only, via direct per-product split of the ACT row (needs raw
    # row cells, same [손실요소외,손실요소,LIC] x 5-product layout confirmed for this era).
    for r in t_act.rows:
        if _MA_ACT4_ROW in "".join(r[:2]):
            from scripts.pl_breakdown.common import _row_nums
            act_nums = _row_nums(r)
            break
    else:
        act_nums = None
    if act_nums and len(act_nums) % 3 == 0:
        loss_ext = act_nums[0::3]
        loss_elem = act_nums[1::3]
        lic = act_nums[2::3]
        cand_a = sum(lic)
        print(f"  손실요소외 all zero: {all(v == 0 for v in loss_ext)}  values={loss_ext}")
        print(f"  candidate A (LIC-only) = {cand_a:,.0f}")
        print(f"  A - B = {cand_a - cand_b:,.6f}  "
              f"({'IDENTICAL' if abs(cand_a - cand_b) < 0.5 else 'DIFFER'})")
        act_loss_elem_sum = sum(loss_elem)
        print(f"  boundary check: 표3 손실요소열 합={act_loss_elem_sum:,.0f}  vs  "
              f"표2 손실요소배분액행 합={loss_alloc:,.0f}  "
              f"-> {'MATCH' if abs(act_loss_elem_sum - loss_alloc) < 0.5 else 'MISMATCH'} "
              f"(diff={act_loss_elem_sum - loss_alloc:,.6f})")

    item6 = (exp - cand_b) / 1e6
    print(f"  item6 (candidate B / NH formula) = {item6:,.6f} 백만원")

    total7 = sum(v for v in (_ma_row_sum(t_exp, c) for c in ALT_7COMP_ROWS) if v is not None)
    rev_lump = _ma_row_sum(t_act, "보험수익")
    check_a = rev_lump is not None and abs(abs(total7) - abs(rev_lump)) < 1.0
    print(f"  check A (internal): total7={total7:,.0f}  rev_lump(표3 보험수익 lump)={rev_lump:,.0f}"
          f"  diff={total7 + rev_lump:,.6f}  -> {check_a}")
    # note: rev_lump is negative (revenue shown as a negative/contra in this rollforward,
    # matching row[2] sign in the raw dump) so compare abs() as production code does.

    anchor = _ma_tier1_ins_rev(ofs_tables)
    check_b = anchor is not None and abs(abs(total7) - abs(anchor)) < 1.0
    print(f"  check B (Tier-1 anchor): anchor(별도 일반보험서비스수익)={anchor}"
          f"  diff={total7 - anchor if anchor else None}  -> {check_b}")

    print(f"  GATE: {'PASS' if (check_a and check_b) else 'FAIL -> would abstain'}")


for label, path in QUARTERS:
    try_quarter(label, path)
