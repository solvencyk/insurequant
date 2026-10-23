# -*- coding: utf-8 -*-
"""read-only: dump the leaf table containing a physical line (1-based): header paths/cells and rows. usage: a05_dump_table_at.py <rel xml path> <line> [maxrows]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from abl_lib import *  # noqa

sys.stdout.reconfigure(encoding="utf-8")
rel, ln = sys.argv[1], int(sys.argv[2])
maxrows = int(sys.argv[3]) if len(sys.argv) > 3 else 60
L = lines_of(rel)
for (a, b) in all_tables(L):
    if a + 1 <= ln <= b + 1:
        print(f"table L{a + 1}-{b + 1}")
        ts = [t for t in titles(L) if t[0] < a]
        print("  nearest TITLE above:", ts[-1][1] if ts else None, "@", ts[-1][0] + 1 if ts else None)
        # context lines above (non-empty text lines before the table)
        ctx = []
        k = a - 1
        while k > 0 and len(ctx) < 4:
            t = clean(L[k])
            if t:
                ctx.append((k + 1, t[:160]))
            k -= 1
        print("  context above:", list(reversed(ctx)))
        u = unit_above(L, a + 1, span=60)
        print("  unit:", u)
        for r in table_rows(L, a, b)[:maxrows]:
            cs = r["cells"]
            print(f"  TR{r['tr']}: " + " | ".join(f"{c['text']}@{c['line']}" for c in cs))
        break
else:
    print("no leaf table contains that line")
