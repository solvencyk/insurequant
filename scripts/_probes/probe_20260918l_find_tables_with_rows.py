# -*- coding: utf-8 -*-
"""Find every parsed table containing a row whose LABEL matches a regex, print index,
caption, basis, and the matching rows only.

Usage: probe_20260918l_find_tables_with_rows.py KR0094 2023.1Q "보험영업수익|보험수익"
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_pl_breakdown as B  # noqa: E402
from scripts.pl_breakdown.tier1 import _header_blob, _is_income_statement  # noqa: E402
from scripts.pl_breakdown.common import _label  # noqa: E402

code, quarter, pat = sys.argv[1], sys.argv[2], sys.argv[3]
RE = re.compile(pat)

dirs = B.discover_filings().get(code, {}).get(quarter)
tables = []
for d in dirs:
    for x in B._xmls_in(d):
        try:
            tables.extend(B._tag_basis(
                list(B._iter_tables_by_basis(Path(x), B._iter_tables_with_context)), x))
        except Exception:
            pass
print(f"{code} {quarter}: {len(tables)} tables; pattern={pat}")
n = 0
for i, t in enumerate(tables):
    rows = list(getattr(t, "rows", []) or [])
    hits = [r for r in rows if RE.search(_label(r) or "")]
    if not hits:
        continue
    n += 1
    print(f"\n[{i}] basis={getattr(t,'_basis',None)} IS={_is_income_statement(t)} "
          f"cap={(getattr(t,'caption','') or '')[:110]}")
    print(f"     hdr={_header_blob(t)[:160]}")
    for r in hits[:14]:
        print("     ", repr(list(r))[:200])
print(f"\n({n} tables matched)")
