"""KR0079 all-quarters regression for the _ma_find_product_table tie-break fix
(inbox/parser/20260830T0000Z). For every KR0079 filing dir, replicate the OLD (pre-fix,
no unresolvable-tie guard) candidate pick and compare it against the NEW (patched,
imported) `_ma_find_product_table` for both the EXP and ACT needles. Any quarter where
they diverge get flagged -- the ticket's own numbered request #2 requires confirming this
fix does not silently change any already-working quarter. Read-only, no master touched."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _iter_tables_by_basis  # noqa: E402
from scripts.pl_breakdown.companies import (  # noqa: E402
    _MA_ACT4_ROW, _MA_EXP4_ROW_VARIANTS, _ma_find_product_table, _ma_yesilcha_direct,
)
from scripts.pl_breakdown.tier1 import _header_blob  # noqa: E402
from scripts.build_pl_breakdown import _xmls_in, discover_filings  # noqa: E402

_SOURCELINE_CAP = 65535


def old_pick(ofs_tables, row_needle):
    """Pre-fix replica: sort by line_no, return cands[0], no tie guard."""
    needles = (row_needle,) if isinstance(row_needle, str) else row_needle
    cands = [t for t in ofs_tables
              if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)
              and any(any(n in "".join(r[:2]) for n in needles) for r in t.rows)]
    cands.sort(key=lambda t: t.line_no)
    return cands[0] if cands else None


filings = discover_filings()
kr0079_dirs = filings.get("KR0079", {})
print(f"KR0079 quarters found: {sorted(kr0079_dirs.keys())}\n")

any_diff = False
for q in sorted(kr0079_dirs.keys()):
    dirs = kr0079_dirs[q]
    xmls = []
    for d in dirs:
        xmls.extend(_xmls_in(d))
    if not xmls:
        print(f"{q}: no xml, skip")
        continue
    tables = []
    for x in xmls:
        tables.extend(_tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
    ofs_tables = _prefer_ofs(tables)

    old_exp = old_pick(ofs_tables, _MA_EXP4_ROW_VARIANTS)
    old_act = old_pick(ofs_tables, _MA_ACT4_ROW)
    new_exp = _ma_find_product_table(ofs_tables, _MA_EXP4_ROW_VARIANTS)
    new_act = _ma_find_product_table(ofs_tables, _MA_ACT4_ROW)

    def key(t):
        return None if t is None else (t.line_no, tuple(tuple(r) for r in t.rows))

    exp_same = key(old_exp) == key(new_exp)
    act_same = key(old_act) == key(new_act)
    item6_old = None
    item6_new = _ma_yesilcha_direct(tables)
    flag = "" if (exp_same and act_same) else "  <-- DIVERGES"
    print(f"{q}: old_exp_line={old_exp.line_no if old_exp else None} "
          f"new_exp_line={new_exp.line_no if new_exp else None}  "
          f"old_act_line={old_act.line_no if old_act else None} "
          f"new_act_line={new_act.line_no if new_act else None}  "
          f"item6(new)={item6_new}{flag}")
    if not (exp_same and act_same):
        any_diff = True

print("\nANY DIVERGENCE:", any_diff)
