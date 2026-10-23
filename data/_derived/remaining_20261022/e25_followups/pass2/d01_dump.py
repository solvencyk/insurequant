# -*- coding: utf-8 -*-
"""pass2 d01 (read-only): dump the separate-notes tables of a filing whose row labels contain ALL the given needles (space-normalised), with every numeric cell and its physical line.
usage: d01_dump.py CODE FY needle1,needle2,... [--all] [--cap REGEX]      (--all = search statement tables too, not only the separate notes)"""
import re
import sys

import p2lib as P

sys.stdout.reconfigure(encoding="utf-8")
code, fy, needles = sys.argv[1], sys.argv[2], [P.nl(x) for x in sys.argv[3].split(",")]
use_all = "--all" in sys.argv
cap_re = sys.argv[sys.argv.index("--cap") + 1] if "--cap" in sys.argv else None
if use_all:
    path, lines, tabs = P.load_all(code, fy)
    s0 = 0
else:
    path, lines, s0, tabs = P.load(code, fy)
print(f"##### {code} {fy} {P.M.rel(path)} separate notes start L{s0}, {len(tabs)} tables")
hits = 0
for t, rows in tabs:
    labs = [P.lab(r) for r in rows]
    blob = "|".join(labs)
    if not all(any(n in x for x in labs) for n in needles):
        continue
    if cap_re and not re.search(cap_re, P.nl(t["caption"] or "")):
        continue
    hits += 1
    P.show(t, rows, lines, tag=f"hit{hits}")
print("hits", hits)
