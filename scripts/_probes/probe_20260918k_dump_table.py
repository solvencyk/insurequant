# -*- coding: utf-8 -*-
"""Dump one specific parsed table by index.
Usage: probe_20260918k_dump_table.py KR0069 2023.1Q 389 [389 ...]
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_pl_breakdown as B  # noqa: E402
from scripts.pl_breakdown.tier1 import _header_blob, _is_income_statement  # noqa: E402
from scripts.pl_breakdown.common import _label  # noqa: E402

code, quarter = sys.argv[1], sys.argv[2]
idxs = [int(a) for a in sys.argv[3:]]

dirs = B.discover_filings().get(code, {}).get(quarter)
tables = []
for d in dirs:
    for x in B._xmls_in(d):
        try:
            tables.extend(B._tag_basis(
                list(B._iter_tables_by_basis(Path(x), B._iter_tables_with_context)), x))
        except Exception:
            pass

for i in idxs:
    t = tables[i]
    print(f"\n===== [{i}] basis={getattr(t,'_basis',None)} IS={_is_income_statement(t)} =====")
    print("caption:", (getattr(t, 'caption', '') or '')[:300])
    print("header :", _header_blob(t)[:300])
    for r in t.rows:
        print("   ", repr(list(r))[:230])
