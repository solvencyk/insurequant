# -*- coding: utf-8 -*-
"""Read-only: reconstruct table rows from fitz word coordinates for a PDF page range.

usage: probe_20260824_reaudit_rowdump.py <pdf> <page1,page2,...>   (1-based pages)
"""
import sys, io
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

pdf = sys.argv[1]
pages = [int(x) for x in sys.argv[2].split(",")]
doc = fitz.open(pdf)
for pno in pages:
    page = doc[pno - 1]
    words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
    print("=" * 120)
    print(f"### PAGE {pno}  (words={len(words)}, chars={len(page.get_text())})")
    rows = {}
    for w in words:
        key = round(w[1] / 3.0)  # 3pt row bucket
        rows.setdefault(key, []).append(w)
    for key in sorted(rows):
        ws = sorted(rows[key], key=lambda w: w[0])
        line = "  ".join(f"{w[4]}@{w[0]:.0f}" for w in ws)
        print(f"y{key*3:5.0f} | {line}")
doc.close()
