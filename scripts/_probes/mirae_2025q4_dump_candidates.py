"""KR0079 2025.4Q -- full dump of the 4 relevant 5-product candidate tables (2x EXP-alt, 2x
ACT) found in mirae_2025q4_investigate.py, all tied at line_no=65535 (sentinel from whichever
attachment XML they came from -- so the usual 'lowest line_no = 당기' tie-break is meaningless
here). Need to see the actual row values to tell which of each pair is 당기 vs 전기(비교), and
check both pairings against the Tier-1 anchor to find the one that's genuinely 당기. Read-only.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _iter_tables_by_basis, _row_nums  # noqa: E402
from scripts.pl_breakdown.companies import (  # noqa: E402
    _MA_ACT4_ROW, _MA_EXP4_ROW_ALT, _MA_7COMP_ROWS, _ma_row_sum, _ma_tier1_ins_rev,
)
from scripts.build_pl_breakdown import _xmls_in  # noqa: E402
from scripts.pl_breakdown.tier1 import _header_blob  # noqa: E402

D = ROOT / "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664"
xmls = _xmls_in(str(D))
tables = []
for x in xmls:
    tables.extend(_tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
ofs_tables = _prefer_ofs(tables)

exp_cands = [t for t in ofs_tables
             if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)
             and any(_MA_EXP4_ROW_ALT in "".join(r[:2]) for r in t.rows)]
act_cands = [t for t in ofs_tables
             if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)
             and any(_MA_ACT4_ROW in "".join(r[:2]) for r in t.rows)]
print(f"exp_cands={len(exp_cands)}  act_cands={len(act_cands)}")

anchor = _ma_tier1_ins_rev(ofs_tables)
print(f"\nTier-1 anchor (별도 일반보험서비스수익, 당기 YTD) = {anchor:,.0f}" if anchor else "anchor=None")

for i, t in enumerate(exp_cands):
    print(f"\n=== EXP candidate #{i} (line={t.line_no}) ===")
    for r in t.rows:
        print(f"  {r}")
    total7 = sum(v for v in (_ma_row_sum(t, c) for c in _MA_7COMP_ROWS) if v is not None)
    print(f"  total7 = {total7:,.0f}")

for i, t in enumerate(act_cands):
    print(f"\n=== ACT candidate #{i} (line={t.line_no}) ===")
    for r in t.rows:
        print(f"  {r}")
    rev_lump = _ma_row_sum(t, "보험수익")
    print(f"  rev_lump(보험수익) = {rev_lump}")

print("\n=== cross-pairing check (which EXP/ACT combo reconciles?) ===")
for i, te in enumerate(exp_cands):
    total7 = sum(v for v in (_ma_row_sum(te, c) for c in _MA_7COMP_ROWS) if v is not None)
    for j, ta in enumerate(act_cands):
        rev_lump = _ma_row_sum(ta, "보험수익")
        ok_a = rev_lump is not None and abs(abs(total7) - abs(rev_lump)) < 1.0
        ok_b = anchor is not None and abs(abs(total7) - abs(anchor)) < 1.0
        print(f"  EXP#{i} (total7={total7:,.0f}) x ACT#{j} (rev_lump={rev_lump}): "
              f"check_a={ok_a}  check_b(anchor)={ok_b}")
