# -*- coding: utf-8 -*-
"""read-only: dump the separate-basis 4-2 statement of one ABL filing: header cells + each row's label and value cells with lines. usage: a04_dump_stmt.py <rel xml path> [title regex]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from abl_lib import *  # noqa

sys.stdout.reconfigure(encoding="utf-8")
rel = sys.argv[1]
title_re = sys.argv[2] if len(sys.argv) > 2 else r"^4-2\.\s*포괄손익계산서"
L = lines_of(rel)
a, b = section_range(L, title_re)
print(f"section lines {a + 1}..{b + 1}, unit {unit_above(L, a + 40, span=60)}")
for (ta, tb) in all_tables(L):
    if not (a <= ta <= b):
        continue
    rows = table_rows(L, ta, tb)
    print(f"-- table L{ta + 1}-{tb + 1}: {len(rows)} rows")
    for r in rows:
        cs = r["cells"]
        if not cs:
            continue
        lab = cs[0]["text"]
        vals = [(c["text"], c["line"]) for c in cs[1:]]
        print(f"  TR{r['tr']} [{cs[0]['tag']}] {lab!r} | " + " | ".join(f"{t}@{ln}" if t else f"_@{ln}" for t, ln in vals))
