"""KR0079 2025.4Q (annual) -- investigate why the ALT-tuple gate FAILs here (sweep found
t_exp/t_act BOTH landing on line=65535 with check_a=False -- suspicious, needs a real look).
Coordinator asked: does 2025.4Q resolve under the same variant tuple that fixed 2026.1Q? If
not, what label does it actually use?

Key difference from the single-file probes used so far: this dir has THREE xml files (main +
_00760 + _00761 attachments), and the REAL production path (build_pl_breakdown.py's
_xmls_in()/parse_filing()) reads ALL of them, not just the main one. Redo the search across
all three, not just the hardcoded single file the old sweep script used.
Read-only.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _iter_tables_by_basis, _row_nums  # noqa: E402
from scripts.pl_breakdown.companies import (  # noqa: E402
    _MA_ACT4_ROW, _MA_EXP4_ROW, _MA_EXP4_ROW_ALT, _MA_EXP4_ROW_VARIANTS,
    _ma_find_product_table, _ma_yesilcha_direct,
)
from scripts.build_pl_breakdown import _xmls_in  # noqa: E402
from scripts.pl_breakdown.tier1 import _header_blob  # noqa: E402

D = ROOT / "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664"
xmls = _xmls_in(str(D))
print(f"_xmls_in({D.name}) -> {len(xmls)} files:")
for x in xmls:
    print(f"  {x}  ({Path(x).stat().st_size:,} bytes)")

# Reproduce parse_filing()'s exact aggregation: iterate every xml file, tag basis, concat.
tables = []
for x in xmls:
    try:
        tables.extend(_tag_basis(
            list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
    except Exception as e:
        print(f"  ERROR on {x}: {e}")
print(f"\ntotal tables across all {len(xmls)} files: {len(tables)}")
ofs_tables = _prefer_ofs(tables)
print(f"ofs tables: {len(ofs_tables)}")

# production gate, across the FULL multi-file table set (not just the main xml alone)
prod_item6 = _ma_yesilcha_direct(tables)
print(f"\nPRODUCTION _ma_yesilcha_direct(all 3 files' tables) = {prod_item6}")

t_exp = _ma_find_product_table(ofs_tables, _MA_EXP4_ROW_VARIANTS)
t_act = _ma_find_product_table(ofs_tables, _MA_ACT4_ROW)
print(f"\nt_exp(ALT variants) line={t_exp.line_no if t_exp else None} "
      f"caption={t_exp.caption if t_exp else None!r}")
print(f"t_act line={t_act.line_no if t_act else None} caption={t_act.caption if t_act else None!r}")

# how many 5-product (사망보험+건강보험 cue) OFS tables exist at all, and do ANY of them
# contain the ACT needle / either EXP needle?
cands_5prod = [t for t in ofs_tables
               if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)]
print(f"\ntotal OFS tables with 사망보험+건강보험 cue: {len(cands_5prod)}")
for t in cands_5prod:
    has_act = any(_MA_ACT4_ROW in "".join(r[:2]) for r in t.rows)
    has_exp_orig = any(_MA_EXP4_ROW in "".join(r[:2]) for r in t.rows)
    has_exp_alt = any(_MA_EXP4_ROW_ALT in "".join(r[:2]) for r in t.rows)
    first_labels = [(r[0] if r else "") for r in t.rows[:4]]
    print(f"  line={t.line_no} caption={t.caption[:50]!r} n_rows={len(t.rows)} "
          f"has_ACT={has_act} has_EXP_orig={has_exp_orig} has_EXP_alt={has_exp_alt} "
          f"first_row_labels={first_labels}")
