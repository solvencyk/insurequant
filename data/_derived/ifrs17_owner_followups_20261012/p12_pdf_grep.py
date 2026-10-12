# -*- coding: utf-8 -*-
"""Read-only: find pages of a PDF whose text contains ALL given keywords. Usage: p12 <pdf> <kw> [<kw> ...]"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import fitz
doc = fitz.open(sys.argv[1])
kws = sys.argv[2:]
print("pages:", len(doc))
for i, pg in enumerate(doc, 1):
    t = pg.get_text("text")
    if all(k in t for k in kws):
        print("page", i, "chars", len(t))
