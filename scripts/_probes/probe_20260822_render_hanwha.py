# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1])
pdf = ROOT / "data/disclosure/FY2025_Q2/raw/KR0068_한화생명.pdf"
doc = fitz.open(pdf)
print("pages", doc.page_count)
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "공통적용" in t and "보완자본" in t and "한도" in t:
        print("match idx", i)
        pix = doc[i].get_pixmap(dpi=240)
        pix.save(str(OUT / "hanwha_2025q2.png"))
        print(t)
doc.close()
