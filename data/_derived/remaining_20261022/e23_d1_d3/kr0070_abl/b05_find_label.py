# -*- coding: utf-8 -*-
"""read-only: find leaf tables of a KR0070 filing that contain a row label substring and print them (cells with physical lines).
usage: b05_find_label.py <rel xml path> <label substring> [maxrows]   (stdlib only; reuses the helper copy abl_lib.py of this folder)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from abl_lib import *  # noqa

sys.stdout.reconfigure(encoding="utf-8")
rel, needle = sys.argv[1], sys.argv[2]
maxrows = int(sys.argv[3]) if len(sys.argv) > 3 else 40
L = lines_of(rel)
nd = nspace(needle)
ts = titles(L)
for (a, b) in all_tables(L):
    rows = table_rows(L, a, b)
    hit = [r for r in rows if r["cells"] and nd in nspace(r["cells"][0]["text"])]
    if not hit:
        continue
    near = [t for t in ts if t[0] < a]
    ctx, k = [], a - 1
    while k > 0 and len(ctx) < 3:
        t = clean(L[k])
        if t:
            ctx.append((k + 1, t[:140]))
        k -= 1
    print(f"== table L{a + 1}-{b + 1} unit {unit_above(L, a + 1, 80)} | section {near[-1][1][:40] if near else None} | ctx {list(reversed(ctx))}")
    for r in rows[:maxrows]:
        cs = r["cells"]
        print(f"   TR{r['tr']}: " + " | ".join(f"{c['text'][:48]}@{c['line']}" for c in cs))
