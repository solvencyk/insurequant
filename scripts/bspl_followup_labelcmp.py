#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare the ordered raw row labels of the bs_full tables of several filings of one company (read-only).
   usage: bspl_followup_labelcmp.py KR0004 2025.1Q 2025.2Q 2025.3Q 2026.1Q"""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from bspl_granularity import stage_b as B  # noqa: E402

def norm(s):
    return re.sub(r"\s+", "", s)

code, qs = sys.argv[1], sys.argv[2:]
lab = {}
for q in qs:
    doc = B.load_tables(code, q)
    ts = B.pick_tables(doc, "bs_full") if doc else []
    if not ts:
        print(q, "no bs_full")
        continue
    t = ts[0]
    lab[q] = [norm(r["label"]) for r in t["rows"]]
    print(q, "p%s" % t["page"], "rows", len(t["rows"]), "unit", t.get("unit"), "cols", max((len(r["vals"]) for r in t["rows"]), default=0), "form", B.table_form(t))
base = qs[0]
for q in qs[1:]:
    if q in lab and base in lab:
        a, b = lab[base], lab[q]
        print(f"  {base} vs {q}: identical={a == b}  only_in_{base}={[x for x in a if x not in b]}  only_in_{q}={[x for x in b if x not in a]}")
