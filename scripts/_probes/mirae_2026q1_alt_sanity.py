"""Quick sanity check for KR0079 2026.1Q's newly-matching t_exp (via the ALT needle found for
2025.2Q/2025.3Q) -- confirms which needle matched and dumps the EXP4 row so the "bonus" finding
reported to orchestrator (out of this ticket's explicit 2-quarter scope, NOT patched into any
master) is grounded in an actual read, not just the aggregate sweep check. Read-only.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _iter_tables_by_basis, _row_nums  # noqa: E402
from scripts.pl_breakdown.tier1 import _header_blob  # noqa: E402

_MA_EXP4_ROW = "발생한 보험금 및 그 밖의 발생한 보험서비스비용을 통한 증가"
_MA_EXP4_ROW_ALT = "발생한 보험금 및 그 밖의 발생한 보험서비스비용에 따른 증가분"

xml_path = ROOT / "data/dart/FY2026_Q1/raw/KR0079_미래에셋생명/20260529001897.xml"
tables = list(_tag_basis(
    list(_iter_tables_by_basis(xml_path, _iter_tables_with_context)), xml_path))
ofs_tables = _prefer_ofs(tables)

cands = [t for t in ofs_tables
          if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)
          and any(_MA_EXP4_ROW_ALT in "".join(r[:2]) for r in t.rows)]
cands.sort(key=lambda t: t.line_no)
print(f"ALT candidates: {len(cands)}")
for t in cands[:1]:
    print(f"line={t.line_no} caption={t.caption!r}")
    for r in t.rows:
        if _MA_EXP4_ROW_ALT in "".join(r[:2]):
            print("EXP4 row:", r)
            print("nums:", _row_nums(r), "sum=", sum(_row_nums(r)))
        if "손실요소배분액" in "".join(r[:2]):
            print("loss_alloc row:", r)

orig_cands = [t for t in ofs_tables
          if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)
          and any(_MA_EXP4_ROW in "".join(r[:2]) for r in t.rows)]
print(f"\nORIGINAL needle candidates: {len(orig_cands)}")
