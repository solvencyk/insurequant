# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1])
pdf = ROOT / "data/disclosure/FY2026_Q1/raw/KR0087_동양생명.pdf"
doc = fitz.open(pdf)
for i in [6, 7]:
    pix = doc[i].get_pixmap(dpi=200)
    pix.save(str(OUT / f"dy_toc_p{i}.png"))
doc.close()
print("done")
