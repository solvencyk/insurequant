# -*- coding: utf-8 -*-
"""Read-only: render PDF pages to PNG for visual confirmation.
usage: probe.py <pdf> <pages> <outprefix> [dpi] [cliptop,clipbot fraction]
"""
import sys, io
import fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
pdf, pages, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 220
doc = fitz.open(pdf)
for p in [int(x) for x in pages.split(",")]:
    page = doc[p - 1]
    pm = page.get_pixmap(dpi=dpi)
    out = f"{prefix}_p{p}.png"
    pm.save(out)
    print("wrote", out, pm.width, "x", pm.height)
doc.close()
