# -*- coding: utf-8 -*-
"""a05 (read-only): print the full content (caption / header / first column / 합계 row) of selected candidate blocks.
Usage: a05_show_blocks.py <company> <rcept> <line_no> [<line_no> ...] [--rows N]"""
from __future__ import annotations

import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
sys.path.insert(0, str(W))
sys.stdout.reconfigure(encoding="utf-8")
from amortlib import V, iter_files  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
nrows = 40
if "--rows" in sys.argv:
    nrows = int(sys.argv[sys.argv.index("--rows") + 1])
    args = [a for a in args if a != str(nrows)]
company, rcept, lines = args[0], args[1], {int(x) for x in args[2:]}
for co, rc, p, blocks in iter_files():
    if co != company or rc != rcept:
        continue
    for b in blocks:
        if int(b.get("line_no") or 0) in lines:
            print("=" * 100)
            print("line", b.get("line_no"), b.get("_source_xml"), "score", b.get("score"), "form", b.get("form_type"))
            print("caption:", b.get("caption"))
            print("header :", b.get("header"))
            print("footnotes:", b.get("footnotes"))
            for r in (b.get("rows") or [])[:nrows]:
                print("   ", [str(c)[:14] for c in r][:20])
