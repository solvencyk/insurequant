# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1])
pdf = ROOT / "data/disclosure/FY2023_Q2/raw/KR0080_에이아이에이생명보험.pdf"
doc = fitz.open(pdf)
for i in [7, 8]:
    pix = doc[i].get_pixmap(dpi=240)
    pix.save(str(OUT / f"aia_2023q2_p{i}.png"))
    print("saved", i)
doc.close()
