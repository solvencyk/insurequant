# -*- coding: utf-8 -*-
import io, sys, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
pdfs = glob.glob(ROOT + "data/disclosure/FY2026_Q2/*/KR1098_*.pdf")
doc = fitz.open(pdfs[0])
page = doc.load_page(32)
clip = fitz.Rect(60, 240, 560, 400)  # around both label columns + numbers
mat = fitz.Matrix(480/72, 480/72)  # extra high dpi since region is small
pix = page.get_pixmap(matrix=mat, clip=clip)
out = ROOT + "artifacts/_kr1098_2026q2_labelzoom_480dpi.png"
pix.save(out)
print("saved", out, pix.width, "x", pix.height)
doc.close()
