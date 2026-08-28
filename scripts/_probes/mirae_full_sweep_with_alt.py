"""Full-quarter sweep (2023.2Q..2026.2Q) simulating the proposed alt-needle-aware
_ma_yesilcha_direct BEFORE touching companies.py, to check for regressions (2026.2Q must stay
identical) and to see whether any quarter OTHER than 2025.2Q/2025.3Q would newly start passing
(out of this ticket's explicit scope -- would need separate scrutiny before filling, not just
silently accepted). Pure preview -- does not modify companies.py or any master. Reuses every
production helper except _ma_row_sum/_ma_find_product_table, which are reimplemented here with
tuple-of-needle-variants support to preview the change before it's actually made.
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
from scripts.pl_breakdown.tier1 import _header_blob, _ytd_col  # noqa: E402
from scripts.pl_breakdown.companies import _label  # noqa: E402

_MA_EXP4_ROW = "발생한 보험금 및 그 밖의 발생한 보험서비스비용을 통한 증가"
_MA_EXP4_ROW_ALT = "발생한 보험금 및 그 밖의 발생한 보험서비스비용에 따른 증가분"
_MA_EXP4_ROW_VARIANTS = (_MA_EXP4_ROW, _MA_EXP4_ROW_ALT)
_MA_ACT4_ROW = "발생한 보험금 및 기타 보험서비스비용"
_MA_7COMP_ROWS = (
    _MA_EXP4_ROW_VARIANTS,
    "비금융위험에 대한 위험조정의 변동분",
    ("보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익",
     "서비스의 이전으로 당기손익에 인식한 보험계약마진"),
    "손실요소배분액",
    ("경험 조정을 통한 증가", "경험조정에 따른 증가분(감소분), 보험계약부채(자산)"),
    "기타 변동에 의한 증가",
    "보험취득 현금흐름의 회수와 관련되는 보험료",
)


def _row_sum(t, needle):
    needles = (needle,) if isinstance(needle, str) else needle
    for r in t.rows:
        joined = "".join(r[:2])
        if any(n in joined for n in needles):
            nums = _row_nums(r)
            if nums:
                return sum(nums)
    return None


def _find_product_table(ofs_tables, row_needle):
    needles = (row_needle,) if isinstance(row_needle, str) else row_needle
    cands = [t for t in ofs_tables
              if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)
              and any(any(n in "".join(r[:2]) for n in needles) for r in t.rows)]
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
    print(f"\n=== {label}: {xml_path.name} ===")
    if not xml_path.exists():
        print("  [xml not on disk]")
        return
    tables = list(_tag_basis(
        list(_iter_tables_by_basis(xml_path, _iter_tables_with_context)), xml_path))
    ofs_tables = _prefer_ofs(tables)

    t_exp = _find_product_table(ofs_tables, _MA_EXP4_ROW_VARIANTS)
    t_act = _find_product_table(ofs_tables, _MA_ACT4_ROW)
    if t_exp is None or t_act is None:
        print(f"  table not found: t_exp={t_exp is not None} t_act={t_act is not None}")
        return

    exp = _row_sum(t_exp, _MA_EXP4_ROW_VARIANTS)
    loss_alloc = _row_sum(t_exp, "손실요소배분액")
    full_row = _row_sum(t_act, _MA_ACT4_ROW)
    if exp is None or loss_alloc is None or full_row is None:
        print(f"  row missing: exp={exp} loss_alloc={loss_alloc} full_row={full_row}")
        return
    act = full_row - loss_alloc
    item6 = (exp - act) / 1e6

    total7 = sum(v for v in (_row_sum(t_exp, c) for c in _MA_7COMP_ROWS) if v is not None)
    rev_lump = _row_sum(t_act, "보험수익")
    check_a = rev_lump is not None and abs(abs(total7) - abs(rev_lump)) < 1.0
    anchor = _tier1_anchor(ofs_tables)
    check_b = anchor is not None and abs(abs(total7) - abs(anchor)) < 1.0
    gate = check_a and check_b
    print(f"  t_exp line={t_exp.line_no}  t_act line={t_act.line_no}  item6={item6:,.6f}  "
          f"check_a={check_a}  check_b={check_b}  GATE={'PASS' if gate else 'FAIL'}")


try_quarter("2023.2Q", ROOT / "data/dart/FY2023_Q2/raw/KR0079_미래에셋생명/20230814003137.xml")
try_quarter("2023.3Q", ROOT / "data/dart/FY2023_Q3/raw/KR0079_미래에셋생명/20231114002863.xml")
try_quarter("2023.4Q(annual)", ROOT / "data/dart/FY2023_Q4/raw/KR0079_미래에셋생명_20240320002014/20240320002014.xml")
try_quarter("2024.1Q", ROOT / "data/dart/FY2024_Q1/raw/KR0079_미래에셋생명/20240516001903.xml")
try_quarter("2024.2Q", ROOT / "data/dart/FY2024_Q2/raw/KR0079_미래에셋생명/20240814004148.xml")
try_quarter("2024.3Q", ROOT / "data/dart/FY2024_Q3/raw/KR0079_미래에셋생명/20241114002301.xml")
try_quarter("2024.4Q(annual)", ROOT / "data/dart/FY2024_Q4/raw/KR0079_미래에셋생명_20250318001228/20250318001228.xml")
try_quarter("2025.1Q", ROOT / "data/dart/FY2025_Q1/raw/KR0079_미래에셋생명/20250515001717.xml")
try_quarter("2025.2Q", ROOT / "data/dart/FY2025_Q2/raw/KR0079_미래에셋생명/xml/20250814003532.xml")
try_quarter("2025.3Q", ROOT / "data/dart/FY2025_Q3/raw/KR0079_미래에셋생명/xml/20251114002791.xml")
try_quarter("2025.4Q(annual)", ROOT / "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664/20260318001664.xml")
try_quarter("2026.1Q", ROOT / "data/dart/FY2026_Q1/raw/KR0079_미래에셋생명/20260529001897.xml")
try_quarter("2026.2Q", ROOT / "data/dart/FY2026_Q2/raw/KR0079_미래에셋생명/20260814004054.xml")
