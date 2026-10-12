# -*- coding: utf-8 -*-
"""Read-only: dump every table of a RAW DART xml whose header (or first body rows) has >=3 year-bucket cells.
Usage: p05_raw_amort_tables.py <xml path> [caption_substring_filter ...]   (tables are shown when the caption contains ANY filter; default 보험계약마진)"""
import re, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant")
from pathlib import Path
from src.ifrs17.csm_extractor import _iter_tables_with_context, _looks_like_year_bucket

p = Path(sys.argv[1])
filters = sys.argv[2:] or ["보험계약마진"]
n = 0
for t in _iter_tables_with_context(p):
    flat = [c for r in t.header for c in r]
    if not flat and t.rows:
        flat = list(t.rows[0])
    hits = sum(1 for c in flat if _looks_like_year_bucket(c))
    first_col = [r[0] for r in t.rows if r and len(r) > 1]
    body_hits = sum(1 for c in first_col if _looks_like_year_bucket(c))
    if hits < 3 and body_hits < 3:
        continue
    if not any(f in t.caption for f in filters):
        continue
    n += 1
    print("=" * 110)
    print("line", t.line_no, "form", t.form_type, "score", t.score)
    print("caption:", t.caption[:200])
    print("header:", t.header)
    for r in t.rows:
        print("    ", r)
    if t.footnotes:
        print("foot:", [f[:160] for f in t.footnotes])
print("tables shown:", n)
