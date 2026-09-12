#!/usr/bin/env python3
"""Investigation-only probe (writes nothing). Re-derives AIA(KR0080) 2023.4Q and 2024.4Q
item18/19 independently from raw, to cross-check against the already-committed
PL_breakdown.json master (per the owner ticket's ask #6 -- re-confirm, don't just trust the
commit log)."""
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _iter_tables_by_basis, _tag_basis  # noqa: E402
from scripts.pl_breakdown.companies import extract_tier2_aia, _aia_from_statement  # noqa: E402

for fy, q in (("FY2023_Q4", "2023.4Q"), ("FY2024_Q4", "2024.4Q")):
    RAW = f"data/dart/{fy}/raw"
    DIRS = sorted(glob.glob(RAW + "/KR0080_*"))
    print(f"\n{'=' * 70}\n{q}  dirs={DIRS}\n{'=' * 70}")
    tables = []
    for d in DIRS:
        for x in sorted(glob.glob(d + "/*.xml")):
            try:
                tables.extend(_tag_basis(
                    list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
            except Exception as e:
                print("  parse error", x, e)
    print(f"  tables parsed: {len(tables)}")

    cur = extract_tier2_aia(tables, dirs=DIRS)
    print(f"  extract_tier2_aia (production dispatcher) output:")
    for k in sorted(cur):
        print(f"    item{k:2d} = {cur[k]}")

    stmt = _aia_from_statement(tables, DIRS)
    print(f"  _aia_from_statement (statement fallback) output:")
    for k in sorted(stmt):
        print(f"    item{k:2d} = {stmt[k]}")
