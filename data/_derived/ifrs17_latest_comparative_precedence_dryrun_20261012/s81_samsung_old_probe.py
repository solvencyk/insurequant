"""Read-only: inspect the 삼성-style OLD LOB note legs (REV/COST/REREV/RECOST) in a later filing, for the current-year read and for the comparative (flipped) read.
usage: python s81_samsung_old_probe.py KR0008 2024.2Q"""
from __future__ import annotations

import json
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
from scripts.pl_breakdown import companies as C  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

kr, later = sys.argv[1:3]
fy = f"FY{later[:4]}_Q{later[5]}"
dirs = [str(d) for d in sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*"))]
tables = []
for d in dirs:
    for x in BP._xmls_in(d):
        tables.extend(BP._tag_basis(list(BP._iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
print("tables", len(tables))
for i, t in enumerate(tables):
    hb = C._header_blob(t)
    if not hb.startswith("구분") or "장기" not in hb:
        continue
    if "생명" in hb or ("국내" in hb and "해외" in hb) or "배당요소" in hb:
        continue
    secs = C._old_sections(t)
    if not secs:
        continue
    blob = " ".join(C._norm(r[0]) for r in t.rows if r)
    if not any(n in blob for n in C._CSM_OLD) and not any(k in secs for k in ("COST", "REREV")):
        continue
    prior = C._old_prior(tables, i)
    print("-" * 100)
    print(f"table#{i} line={getattr(t, 'line_no', None)} prior={prior} caption={(t.caption or '')[:60]!r} basis={getattr(t, 'basis', None)}")
    print("   header blob:", hb[:200])
    print("   order:", C._old_order(t), "st:", 2 if ("3개월" in hb and "누적" in hb) else 1, "sections:", {k: len(v) for k, v in secs.items()})
    for leg, rows in secs.items():
        tot = C._old_total(rows)
        print(f"   {leg:<7} total row nums: {tot}")
    # prior marker rows in the 2 tables before
    for j in (i - 2, i - 1):
        if 0 <= j < len(tables):
            tj = tables[j]
            print(f"   [prev table#{j}] rows={len(tj.rows)} first={(C._norm(tj.rows[0][0]) if tj.rows and tj.rows[0] else '')[:30]!r} caption={(tj.caption or '')[:40]!r}")
