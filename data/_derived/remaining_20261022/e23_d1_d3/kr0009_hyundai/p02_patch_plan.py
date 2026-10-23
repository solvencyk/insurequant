# -*- coding: utf-8 -*-
"""Patch this folder's planner copy (asserted substitutions, each must hit exactly once).
The shared planner skips items 2 / 7 / 12 for every kind because the life/lotte kinds recompute them from the final legs.  For 현대해상 (kind 'hd') the LOB legs 2 / 13 / 14 of 2023.1Q and
2023.2Q are READ (IR factsheet '(3) UW Income', 장기 / 자동차 / 일반 prior-year cumulative) and nothing recomputes them (out_d = {} for hd), so item 2 must be adopted directly like 13 / 14.
Items 7 / 12 are not read for hd and stay out of scope."""
from pathlib import Path

p = Path(__file__).resolve().parent / "e23_plan.py"
s = p.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:100])
    s = s.replace(a, b)


sub("            if i in (2, 7, 12):\n                continue\n",
    "            if i in (2, 7, 12) and not (co[\"kind\"] == \"hd\" and i == 2 and q in co.get(\"ir_quarters\", [])):\n                continue\n")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok", len(s))
