#!/usr/bin/env python3
"""Investigation-only probe (writes nothing). Dumps RAW (position-preserving, blanks
included) cells of AIA(KR0080) 2025.4Q's 원수 CSM measurement-component table, to resolve
the column layout that the blank-skipping _row_nums() output left ambiguous."""
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _iter_tables_by_basis, _tag_basis, _norm  # noqa: E402

RAW = "data/dart/FY2025_Q4/raw"
DIRS = sorted(glob.glob(RAW + "/KR0080_*"))

tables = []
for d in DIRS:
    for x in sorted(glob.glob(d + "/*.xml")):
        try:
            tables.extend(_tag_basis(
                list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
        except Exception as e:
            print("  parse error", x, e)

# find the FY2025(당기) 원수 table by the 기초=기말-continuity test done in the prior probe:
# 기초 총계 14,909,822 identifies it (see prior probe's table #116).
cand = None
for t in tables:
    cap = t.caption or ""
    if "측정요소별 변동내역" in cap and getattr(t, "_basis", None) == "OFS" \
            and "보험계약부채" in cap:
        # check first 기초 row for the 14,909,822 anchor
        for r in t.rows or []:
            cells = [_norm(c) for c in r]
            if cells and "기초" in cells[0] and "14,909,822" in " ".join(cells):
                cand = t
                break
    if cand:
        break

if cand is None:
    print("NOT FOUND by anchor -- listing all matches instead")
    for t in tables:
        cap = t.caption or ""
        if "측정요소별 변동내역" in cap and getattr(t, "_basis", None) == "OFS" \
                and "보험계약부채" in cap:
            print(cap)
            for r in (t.rows or [])[:3]:
                print("  ", [_norm(c) for c in r])
else:
    print("HEADER ROWS (raw cells):")
    for h in cand.header:
        print("  ", h)
    print("\nBODY ROWS (raw cells, position-preserving):")
    for r in cand.rows or []:
        cells = [_norm(c) for c in r]
        print(f"  {cells}")
