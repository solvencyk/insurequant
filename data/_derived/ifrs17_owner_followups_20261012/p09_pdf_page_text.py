# -*- coding: utf-8 -*-
"""Read-only: print PyMuPDF text (sorted by position) of given 1-based pages. Usage: p09 <pdf> <page> [<page> ...]"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import fitz
doc = fitz.open(sys.argv[1])
print("pages:", len(doc))
for p in sys.argv[2:]:
    pg = doc[int(p) - 1]
    print("=" * 100)
    print("PAGE", p)
    print(pg.get_text("text", sort=True))
