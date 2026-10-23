# -*- coding: utf-8 -*-
"""pass2 d02 (read-only): list the tables of a filing whose raw text contains ALL needles; print rows with numeric cells + physical lines.
usage: d02_find.py CODE FY needle1,needle2,... [--statement] [--maxrows N]    (--statement = also search tables before the separate notes)"""
import sys

import p2lib as P

sys.stdout.reconfigure(encoding="utf-8")
code, fy, needles = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
sep_only = "--statement" not in sys.argv
maxrows = int(sys.argv[sys.argv.index("--maxrows") + 1]) if "--maxrows" in sys.argv else 400
path, lines, s0, tabs = P.tables_with(code, fy, needles, sep_only=sep_only)
print(f"##### {code} {fy} {P.M.rel(path)} separate notes start L{s0}; {len(tabs)} matching tables for {needles}")
for t, rows in tabs:
    P.show(t, rows[:maxrows], lines, tag="match")
