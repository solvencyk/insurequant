#!/usr/bin/env python3
"""악사손해 2023.4Q: 별도 감사보고서 첨부에 손보 Tier-2(장기/자동차/일반) 노트가 있나."""
import sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_pl_breakdown as BP
from src.ifrs17.csm_extractor import _iter_tables_with_context
from scripts.pl_breakdown.common import _tag_basis, _iter_tables_by_basis
from scripts.pl_breakdown.tier2 import extract_tier2_sonbo, extract_tier2_sonbo_structured
from scripts.pl_breakdown.companies import SONBO_HANDLERS, extract_tier2_old, extract_tier2_sonbo_component

rd = sorted((ROOT / "data/dart/FY2023_Q4/raw").glob("KR0049_*"))[0]
tables = []
for x in BP._xmls_in(str(rd)):
    tables += _tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x)
print("tables", len(tables))
hits = 0
for t in tables:
    cap = (t.caption or "")[:90]
    hdr = " ".join(" ".join(str(c) for c in r) for r in (t.header or []))[:120]
    body = " ".join(" ".join(str(c) for c in r) for r in (t.rows or []))
    if ("장기" in hdr or "자동차" in hdr) and ("보험계약마진" in body or "상각" in body):
        hits += 1
        print("=" * 90)
        print("CAP:", cap)
        print("HDR:", hdr)
        for r in (t.rows or [])[:26]:
            print("   ", [str(c)[:22] for c in r][:8])
print("후보 표", hits)
print()
for nm, fn in [("sonbo", extract_tier2_sonbo), ("sonbo_structured", extract_tier2_sonbo_structured),
               ("old", extract_tier2_old), ("component", extract_tier2_sonbo_component),
               ("handler", SONBO_HANDLERS.get("KR0049"))]:
    if fn is None:
        print(f"  {nm:18s} (핸들러 없음)"); continue
    try:
        out = fn(tables)
    except Exception as e:
        out = f"ERR {type(e).__name__}: {e}"
    print(f"  {nm:18s} {out if not isinstance(out, dict) else {k: v for k, v in out.items() if not str(k).startswith('_')}}")
