# -*- coding: utf-8 -*-
"""Read-only: dump ALL tables of a RAW DART xml whose line_no lies in [lo, hi]. Usage: p06 <xml> <lo> <hi>"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant")
from pathlib import Path
from src.ifrs17.csm_extractor import _iter_tables_with_context
p = Path(sys.argv[1]); lo = int(sys.argv[2]); hi = int(sys.argv[3])
for t in _iter_tables_with_context(p):
    if lo <= t.line_no <= hi:
        print("=" * 110)
        print("line", t.line_no, "caption:", t.caption[:200])
        print("header:", t.header)
        for r in t.rows:
            print("    ", r)
        if t.footnotes:
            print("foot:", [f[:160] for f in t.footnotes])
