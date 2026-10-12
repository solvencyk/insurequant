"""Read-only: print every BS-like table (labels 자산총계/부채총계/자본총계) of the annual reports FY<Y>_Q4 and FY<Y+1>_Q4 of one company.
usage: python s75_bs_probe.py KR0001 2024"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _norm  # noqa: E402

kr, y = sys.argv[1], int(sys.argv[2])
for yy in (y, y + 1):
    for rd in sorted((ROOT / "data/dart" / f"FY{yy}_Q4" / "raw").glob(f"{kr}_*")):
        print("=" * 100)
        print(f"FY{yy}", rd.name)
        for x in sorted(rd.rglob("*.xml")):
            for t in _iter_tables_with_context(x):
                labs = {_norm(r[0]).replace(" ", ""): r for r in t.rows if r}
                if "자산총계" in labs and "부채총계" in labs:
                    hdr = [c for r in t.header for c in r][:5]
                    print(f"  {x.name} line {t.line_no} cap={(t.caption or '')[:40]!r} hdr={hdr}")
                    for k in ("자산총계", "부채총계", "자본총계"):
                        if k in labs:
                            print("      ", k, labs[k][1:5])
