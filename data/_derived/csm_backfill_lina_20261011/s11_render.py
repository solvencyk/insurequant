# -*- coding: utf-8 -*-
"""Step 11: render source pages to PNG for a visual check (not part of the load).
usage: s11_render.py FY2026_Q2 93 [dpi]   ->  renders/<FY>_p<N>.png"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "renders"
OUT.mkdir(exist_ok=True)
fy = sys.argv[1]
page_no = int(sys.argv[2])
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 100
pdf = sorted((ROOT / "data" / "disclosure" / fy / "raw").glob("KR0074_*.pdf"))[0]
doc = fitz.open(pdf)
pix = doc[page_no - 1].get_pixmap(dpi=dpi)
dest = OUT / f"{fy}_p{page_no}.png"
pix.save(str(dest))
print(dest, pix.width, pix.height)
