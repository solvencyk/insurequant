"""KR0079 2025.4Q -- confirm the CFS/OFS basis-tagging hypothesis for the wrong-table-pick
ticket (inbox/parser/20260830T0000Z): are the two 'normal' (row-values correct) renderings of
the 18-1 note (raw sourceline 30541/31040, see mirae_2025q4_raw_colspan_dump.py) tagged CFS
(연결) and dropped by `_prefer_ofs`, leaving only the two corrupted (line-shifted) OFS-tagged
copies (raw sourceline >54680, capped to line_no=65535) as the sole 사망보험+건강보험-cue
candidates? Read-only, no master touched."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import (  # noqa: E402
    _tag_basis, _prefer_ofs, _iter_tables_by_basis, _ofs_line_boundary,
)
from scripts.pl_breakdown.companies import _MA_ACT4_ROW, _MA_EXP4_ROW_ALT  # noqa: E402
from scripts.build_pl_breakdown import _xmls_in  # noqa: E402
from scripts.pl_breakdown.tier1 import _header_blob  # noqa: E402

D = ROOT / "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664"
main_xml = D / "20260318001664.xml"
boundary = _ofs_line_boundary(str(main_xml))
print(f"_ofs_line_boundary(main xml) = {boundary}  (SOURCELINE_CAP=65535)")

xmls = _xmls_in(str(D))
tables = []
for x in xmls:
    tables.extend(_tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))

print(f"\ntotal tables (all files, pre-_prefer_ofs): {len(tables)}")

# ALL 5-product-cue candidates BEFORE _prefer_ofs, regardless of basis
all_5prod = [t for t in tables
             if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)]
print(f"5-product-cue candidates BEFORE _prefer_ofs: {len(all_5prod)}")
for t in all_5prod:
    has_act = any(_MA_ACT4_ROW in "".join(r[:2]) for r in t.rows)
    has_exp_alt = any(_MA_EXP4_ROW_ALT in "".join(r[:2]) for r in t.rows)
    print(f"  line_no={t.line_no:>6}  basis={getattr(t, '_basis', '?'):>5}  "
          f"n_rows={len(t.rows):>3}  has_ACT={has_act!s:>5}  has_EXP_alt={has_exp_alt!s:>5}  "
          f"caption={t.caption[:40]!r}")

ofs_tables = _prefer_ofs(tables)
print(f"\ntables AFTER _prefer_ofs: {len(ofs_tables)}")
after_5prod = [t for t in ofs_tables
               if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)]
print(f"5-product-cue candidates AFTER _prefer_ofs: {len(after_5prod)}")
for t in after_5prod:
    print(f"  line_no={t.line_no:>6}  basis={getattr(t, '_basis', '?'):>5}  n_rows={len(t.rows):>3}")
