# -*- coding: utf-8 -*-
"""usage: tdump.py CODE FY 'regex-on-row-labels' [maxrows]   prints separate-notes tables having a row label matching regex"""
import sys, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
import e23_read as E
import s2lib
import s2lib
import e21_t2 as T
code, fy, pat = sys.argv[1:4]
mx = int(sys.argv[4]) if len(sys.argv) > 4 else 60
path = T.main_path(code, fy)
lines, s0, tabs = s2lib.tables_sep2(path)
print(path, "sep notes start", s0, "tables", len(tabs))
for t, rows in tabs:
    labs = [E.lab(r) for r in rows]
    if not any(re.search(pat, x) for x in labs): continue
    cap = E.nl(t["caption"] or "")[:90]
    print(f"--- table@L{t['start']} rows={len(rows)} cap={cap!r}")
    for r in rows[:mx]:
        cells = [(c["text"][:18], c["line"]) for c in r["cells"]]
        print("   ", f"L{r['tr_line']}", " | ".join(f"{a}" for a, b in cells)[:260])
