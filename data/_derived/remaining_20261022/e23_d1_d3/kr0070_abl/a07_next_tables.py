# -*- coding: utf-8 -*-
"""read-only: dump the first N leaf tables that start after a physical line (1-based). usage: a07 <rel> <line> [n] [maxrows]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from abl_lib import *  # noqa

sys.stdout.reconfigure(encoding="utf-8")
rel, ln = sys.argv[1], int(sys.argv[2])
n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
maxrows = int(sys.argv[4]) if len(sys.argv) > 4 else 80
L = lines_of(rel)
cnt = 0
for (a, b) in all_tables(L):
    if a + 1 > ln:
        print(f"== table L{a + 1}-{b + 1} unit {unit_above(L, a + 1, 60)}")
        for r in table_rows(L, a, b)[:maxrows]:
            print(f"  TR{r['tr']}: " + " | ".join(f"{c['text']}@{c['line']}" for c in r["cells"]))
        cnt += 1
        if cnt >= n:
            break
