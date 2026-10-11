#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find tables of a DART body XML whose cell text contains ALL given keywords (read-only).
   usage: bspl_followup_xml_find.py <xml> 키워드1 키워드2 ... [--rows N]"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

args = sys.argv[1:]
mx = 14
if "--rows" in args:
    i = args.index("--rows")
    mx = int(args[i + 1])
    del args[i:i + 2]
xml, kws = Path(args[0]), args[1:]
for t in _iter_tables_with_context(xml):
    txt = " ".join(str(c) for r in t.rows for c in r) + " " + " ".join(str(h) for h in (t.header or []))
    if all(k in txt for k in kws):
        print(f"--- line {t.line_no} rows {len(t.rows)} caption: {(t.caption or '')[:120]!r}")
        print("header:", t.header)
        for i, r in enumerate(t.rows[:mx]):
            print(i, [str(c)[:28] for c in r])
