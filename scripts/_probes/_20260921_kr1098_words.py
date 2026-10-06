# -*- coding: utf-8 -*-
import io, sys, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
pdfs = glob.glob(ROOT + "data/disclosure/FY2026_Q2/*/KR1098_*.pdf")
doc = fitz.open(pdfs[0])
page = doc.load_page(32)
words = page.get_text("words")
for w in words:
    x0, y0, x1, y1, txt = w[0], w[1], w[2], w[3], w[4]
    if txt in ("전", "후", "치", "과", "경") or "전" in txt or "후" in txt:
        print(f"y0={y0:7.2f} y1={y1:7.2f} x0={x0:7.2f} x1={x1:7.2f}  text={txt!r}")
doc.close()
