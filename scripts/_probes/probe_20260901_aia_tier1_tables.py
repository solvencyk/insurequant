"""Dump AIA's 포괄손익계산서 as the PL builder's own table iterator sees it, all 4 years,
and run extract_tier1 on each to see what it returns."""
from __future__ import annotations

import glob
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import os

os.chdir(ROOT)

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _iter_tables_by_basis, _tag_basis  # noqa: E402
from scripts.pl_breakdown.tier1 import extract_tier1  # noqa: E402

DIRS = {
    "2022.4Q": "data/dart/FY2022_Q4/raw/KR0080_에이아이에이생명보험_20230410002773",
    "2023.4Q": "data/dart/FY2023_Q4/raw/KR0080_에이아이에이생명보험_20240409002583",
    "2024.4Q": "data/dart/FY2024_Q4/raw/KR0080_에이아이에이생명보험_20250401000094",
    "2025.4Q": "data/dart/FY2025_Q4/raw/KR0080_에이아이에이생명보험_20260407002100",
}

for q, d in DIRS.items():
    print("=" * 110)
    print(f"### {q}  {d}")
    tables = []
    for x in sorted(glob.glob(d + "/*.xml")):
        try:
            tables.extend(_tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
        except Exception as e:  # noqa: BLE001
            print("   table parse error:", e)
    print(f"   tables parsed: {len(tables)}")
    # find income-statement-looking tables
    for i, t in enumerate(tables):
        cap = (t.caption or "").replace(" ", "")
        flat = " ".join(" ".join(str(c) for c in r) for r in (t.rows or [])[:6])
        if ("포괄손익계산서" in cap or "손익계산서" in cap
                or "보험영업수익" in flat or "보험손익" in flat):
            print(f"\n   --- table[{i}] basis={getattr(t,'basis',None)} caption={t.caption!r}")
            print(f"       header={t.header}")
            for r in (t.rows or [])[:45]:
                print("       " + " | ".join("" if c is None else str(c) for c in r))
    t1 = extract_tier1(tables, code="KR0080")
    print(f"\n   extract_tier1(KR0080) -> {t1}")
