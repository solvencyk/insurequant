# -*- coding: utf-8 -*-
"""Read-only: render one PDF page to PNG. Usage: p32 <pdf> <page> <out.png> [dpi]"""
import sys
import fitz
pdf, page, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 130
doc = fitz.open(pdf)
pix = doc[page - 1].get_pixmap(dpi=dpi)
pix.save(out)
print("saved", out, pix.width, pix.height)
