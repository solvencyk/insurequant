# -*- coding: utf-8 -*-
import io, sys, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
pdfs = glob.glob(ROOT + "data/disclosure/FY2026_Q2/*/KR1098_*.pdf")
doc = fitz.open(pdfs[0])
page = doc.load_page(32)  # 0-indexed page 32 = the rate-sensitivity page
mat = fitz.Matrix(240/72, 240/72)
pix = page.get_pixmap(matrix=mat)
out = ROOT + "artifacts/_kr1098_2026q2_p33_240dpi.png"
import os
os.makedirs(os.path.dirname(out), exist_ok=True)
pix.save(out)
print("saved", out, pix.width, "x", pix.height)
doc.close()
