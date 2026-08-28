"""Standalone test of the planned item6 (원수 예실차) extraction logic for KR0079's Era-2
XBRL note, run against several quarters' raw XML directly (bypassing full discover_filings/
build_pl_breakdown.py), to see which quarters the population-check gates accept BEFORE this
logic is committed into scripts/pl_breakdown/companies.py. Does not touch any master JSON.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import (  # noqa: E402
    _tag_basis, _prefer_ofs, _iter_tables_by_basis, _label, _row_nums,
)
from scripts.pl_breakdown.tier1 import _header_blob, _ytd_col  # noqa: E402

EXP_NEEDLE = "발생한 보험금 및 그 밖의 발생한 보험서비스비용을 통한 증가"
ACT_NEEDLE = "발생한 보험금 및 기타 보험서비스비용"
COMPS = [
    EXP_NEEDLE,
    "비금융위험에 대한 위험조정의 변동분",
    "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익",
    "손실요소배분액",
    "경험 조정을 통한 증가",
    "기타 변동에 의한 증가",
    "보험취득 현금흐름의 회수와 관련되는 보험료",
]


def _row_sum(t, needle):
    for r in t.rows:
        if needle in "".join(r[:2]):
            nums = _row_nums(r)
            if nums:
                return sum(nums)
    return None


def _find_product_table(ofs_tables, needle):
    cands = []
    for t in ofs_tables:
        hb = _header_blob(t)
        if "사망보험" not in hb or "건강보험" not in hb:
            continue
        if any(needle in "".join(r[:2]) for r in t.rows):
            cands.append(t)
    cands.sort(key=lambda t: t.line_no)
    return cands[0] if cands else None


def _tier1_anchor(ofs_tables):
    for t in ofs_tables:
        for r in t.rows:
            if _label(r, 0) == "일반보험서비스수익":
                col = _ytd_col(t)
                nums = _row_nums(r)
                if len(nums) > col:
                    return nums[col]
    return None


def try_quarter(label, xml_path):
    print(f"\n=== {label}: {xml_path} ===")
    if not xml_path.exists():
        print("  [xml not on disk]")
        return
    tables = list(_tag_basis(
        list(_iter_tables_by_basis(xml_path, _iter_tables_with_context)), xml_path))
    ofs_tables = _prefer_ofs(tables)

    t_exp = _find_product_table(ofs_tables, EXP_NEEDLE)
    t_act = _find_product_table(ofs_tables, ACT_NEEDLE)
    if t_exp is None or t_act is None:
        print(f"  table not found: t_exp={t_exp is not None} t_act={t_act is not None}")
        return

    exp = _row_sum(t_exp, EXP_NEEDLE)
    loss_alloc = _row_sum(t_exp, "손실요소배분액")
    full_row = _row_sum(t_act, ACT_NEEDLE)
    if exp is None or loss_alloc is None or full_row is None:
        print(f"  row missing: exp={exp} loss_alloc={loss_alloc} full_row={full_row}")
        return
    act = full_row - loss_alloc
    item6 = (exp - act) / 1e6
    print(f"  exp={exp:,.0f}  full_row={full_row:,.0f}  loss_alloc={loss_alloc:,.0f}  "
          f"act={act:,.0f}  item6={item6:,.6f}")

    total7 = sum(v for v in (_row_sum(t_exp, c) for c in COMPS) if v is not None)
    rev_lump = _row_sum(t_act, "보험수익")
    check_a = rev_lump is not None and abs(abs(total7) - abs(rev_lump)) < 1.0
    print(f"  check A (internal): total7={total7:,.0f} rev_lump={rev_lump} -> {check_a}")

    anchor = _tier1_anchor(ofs_tables)
    check_b = anchor is not None and abs(abs(total7) - abs(anchor)) < 1.0
    print(f"  check B (tier1 anchor): anchor={anchor} -> {check_b}")

    print(f"  GATE: {'PASS -> would emit item6' if (check_a and check_b) else 'FAIL -> abstain'}")


try_quarter("2026.2Q", ROOT / "data/dart/FY2026_Q2/raw/KR0079_미래에셋생명/20260814004054.xml")
try_quarter("2026.1Q", ROOT / "data/dart/FY2026_Q1/raw/KR0079_미래에셋생명/20260529001897.xml")
try_quarter("2025.4Q", ROOT / "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664/20260318001664.xml")
try_quarter("2024.4Q(annual)", ROOT / "data/dart/FY2024_Q4/raw/KR0079_미래에셋생명_20250318001228/20250318001228.xml")
try_quarter("2024.1Q", ROOT / "data/dart/FY2024_Q1/raw/KR0079_미래에셋생명/20240516001903.xml")
try_quarter("2023.2Q", ROOT / "data/dart/FY2023_Q2/raw/KR0079_미래에셋생명/20230814003137.xml")
try_quarter("2023.3Q", ROOT / "data/dart/FY2023_Q3/raw/KR0079_미래에셋생명/20231114002863.xml")
try_quarter("2023.4Q", ROOT / "data/dart/FY2023_Q4/raw/KR0079_미래에셋생명_20240320002014/20240320002014.xml")
try_quarter("2024.2Q", ROOT / "data/dart/FY2024_Q2/raw/KR0079_미래에셋생명/20240814004148.xml")
try_quarter("2024.3Q", ROOT / "data/dart/FY2024_Q3/raw/KR0079_미래에셋생명/20241114002301.xml")
try_quarter("2025.1Q", ROOT / "data/dart/FY2025_Q1/raw/KR0079_미래에셋생명/20250515001717.xml")
