"""Read-only probe: does extract_measurement_tables see the prior-period (전분기) CER table of 현대해상 2024.1Q (line ~44042)?"""
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
from src.ifrs17.measurement_extractor import extract_measurement_tables, to_jsonable  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

x = ROOT / "data/dart/FY2024_Q1/raw/KR0009_현대해상/20240516002153.xml"
print("--- all tables with context near the CER section (line 43700..44600)")
n = 0
for t in _iter_tables_with_context(x):
    ln = getattr(t, "line_no", None)
    if ln and 43700 <= ln <= 44600:
        n += 1
        rows = getattr(t, "rows", [])
        print(ln, repr((getattr(t, "caption", "") or "")[:90]), "rows", len(rows), "hdr", [c for r in getattr(t, "header", [])[:1] for c in r][:5])
print("tables in window", n)
print("--- extract_measurement_tables result lines")
for t in extract_measurement_tables(x, company_name="현대해상"):
    print(t.line_no, repr(t.caption[:80]), "score", t.score, len(t.rows))
