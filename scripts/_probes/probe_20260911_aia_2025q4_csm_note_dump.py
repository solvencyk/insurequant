#!/usr/bin/env python3
"""Investigation-only probe (writes nothing). Dumps the FULL numeric rows of AIA(KR0080)
2025.4Q's genuine CSM/measurement-component roll-forward note table -- both the 원수
(note 18(4)) and 재보험 (note 19(3)) versions -- so item3-8 can be cross-checked against
the audited 포괄손익계산서 statement figures already pulled in the sibling probe."""
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _iter_tables_by_basis, _tag_basis  # noqa: E402
from scripts.pl_breakdown.companies import _row_nums, _lab0  # noqa: E402

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

print(f"total tables: {len(tables)}\n")

targets = []
for i, t in enumerate(tables):
    cap = t.caption or ""
    if "측정요소별 변동내역" in cap and getattr(t, "_basis", None) == "OFS":
        targets.append((i, t))

print(f"OFS-basis '측정요소별 변동내역' tables found: {len(targets)}\n")
for i, t in targets:
    print("=" * 70)
    print(f"table #{i}  caption={t.caption!r}")
    print(f"header={t.header}")
    print("=" * 70)
    for r in t.rows or []:
        lab = _lab0(r)
        nums = _row_nums(r)
        print(f"  {lab!r:55s} nums={nums}")
    print()

# also broaden: any OFS table whose caption mentions '측정요소' at all (catches a possible
# separate '2) 전기' twin the exact-phrase filter above might miss)
print("\n" + "=" * 70)
print("BROADER: any OFS table caption containing '측정요소'")
print("=" * 70)
for i, t in enumerate(tables):
    cap = t.caption or ""
    if "측정요소" in cap and getattr(t, "_basis", None) == "OFS":
        print(f"  table #{i} caption={cap!r} n_rows={len(t.rows or [])}")

# check the reinsurance-side 재보험서비스결과 table too, for item8 cross-check, with values
print("\n" + "=" * 70)
print("재보험계약자산 측정요소별 변동내역 (OFS) -- for item8/9/10/11 cross-check")
print("=" * 70)
for i, t in enumerate(tables):
    cap = t.caption or ""
    if "재보험계약자산의 측정요소별" in cap and getattr(t, "_basis", None) == "OFS":
        print(f"table #{i} caption={cap!r}")
        for r in t.rows or []:
            lab = _lab0(r)
            nums = _row_nums(r)
            print(f"  {lab!r:55s} nums={nums}")
        print()
        break  # first OFS copy only
