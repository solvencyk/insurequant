# -*- coding: utf-8 -*-
"""Dump every 포괄손익계산서-like table (and its row labels) from the raw XML of an orphan
bucket, so 'is the 보험수익/보험비용/재보험 line in the source?' is answered from the
document, not from a keyword count.

Usage: probe_20260918h_income_statement_dump.py KR0069 2023.1Q [substring-filter]
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_pl_breakdown as B  # noqa: E402
from scripts.pl_breakdown.tier1 import _is_income_statement, _header_blob  # noqa: E402
from scripts.pl_breakdown.common import _label  # noqa: E402

code = sys.argv[1]
quarter = sys.argv[2]
want = sys.argv[3] if len(sys.argv) > 3 else None

filings = B.discover_filings()
dirs = filings.get(code, {}).get(quarter)
if not dirs:
    print("no dirs for", code, quarter)
    sys.exit(1)

tables = []
for d in dirs:
    for x in B._xmls_in(d):
        try:
            tables.extend(B._tag_basis(
                list(B._iter_tables_by_basis(Path(x), B._iter_tables_with_context)), x))
        except Exception as e:
            print("parse fail", x, type(e).__name__, e)

print(f"{code} {quarter}: {len(tables)} tables, dirs={dirs}")
KEYS = ("보험수익", "보험서비스비용", "보험비용", "재보험", "보험손익", "보험서비스결과",
        "영업이익", "당기순이익", "분기순이익", "반기순이익")

shown = 0
for i, t in enumerate(tables):
    cap = (getattr(t, "caption", "") or "")[:160]
    rows = list(getattr(t, "rows", []) or [])
    labels = [_label(r) for r in rows]
    blob = " ".join(labels)
    try:
        isis = _is_income_statement(t)
    except Exception:
        isis = None
    hit = any(k in blob for k in KEYS)
    if want and want not in (cap + blob):
        continue
    if not (isis or hit):
        continue
    shown += 1
    print(f"\n--- [{i}] IS={isis} basis={getattr(t,'_basis',None)} ---")
    print(f"    caption: {cap}")
    try:
        print(f"    header : {_header_blob(t)[:240]}")
    except Exception:
        pass
    for r in rows[:80]:
        lab = _label(r)
        if not lab:
            continue
        print(f"      {lab[:46]:<48} {list(r[1:8])}")
print(f"\n(shown {shown} tables)")
