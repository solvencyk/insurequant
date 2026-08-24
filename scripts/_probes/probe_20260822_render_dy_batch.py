# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1])
pdf = ROOT / "data/disclosure/FY2026_Q1/raw/KR0087_동양생명.pdf"
doc = fitz.open(pdf)
for i in range(12, 23):
    pix = doc[i].get_pixmap(dpi=110)  # lower dpi for quick scan
    pix.save(str(OUT / f"dy_scan_p{i:02d}.png"))
doc.close()
print("done")
