"""Read-only: print the income-statement rows (영업이익 / 영업외 / 세전 / 법인세 / 당기순이익 / 보험손익) the production Tier-1 HTML extractor sees in an ORIGINAL filing.
usage: python s94_is_rows_probe.py KR0068 FY2023_Q2"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_pl_breakdown as BP  # noqa: E402
from scripts.pl_breakdown.common import _norm  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

kr, fy = sys.argv[1:3]
dirs = [str(d) for d in sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*"))]
print("dirs", dirs)
tables = []
for d in dirs:
    for x in BP._xmls_in(d):
        tables.extend(BP._tag_basis(list(BP._iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
print("tables", len(tables))
t1 = BP.extract_tier1(tables, code=kr)
print("production Tier-1 (HTML) read:", {k: (round(v, 3) if isinstance(v, (int, float)) else v) for k, v in (t1 or {}).items() if not str(k).startswith("_")})
keys = ("영업이익", "영업외", "세전", "법인세비용차감전", "법인세", "당기순이익", "보험손익", "투자손익")
shown = 0
for i, t in enumerate(tables):
    cap = (t.caption or "")
    hdr = " ".join(c for r in t.header for c in r)[:90]
    hit = [r for r in t.rows if r and any(k in _norm(r[0]).replace(" ", "") for k in keys)]
    if len(hit) >= 4:
        print("-" * 100)
        print(f"table#{i} basis={getattr(t, 'basis', None)} line={getattr(t, 'line_no', None)} caption={cap[:50]!r} header={hdr!r}")
        for r in hit[:14]:
            print("    ", [c[:18] for c in r[:7]])
        shown += 1
        if shown >= 6:
            break
