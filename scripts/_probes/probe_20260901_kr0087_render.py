# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

path = r"data/disclosure/FY2026_Q2/pdf/KR0087_동양생명.pdf"
outdir = r"C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/a2eaf685-d24e-438d-8f71-52ff9b5cfb3b/scratchpad/kr0087_pages"
doc = fitz.open(path)
mat = fitz.Matrix(240/72, 240/72)
for pno in [13,14,15,16,17]:
    page = doc[pno-1]
    pix = page.get_pixmap(matrix=mat)
    outpath = f"{outdir}/p{pno}.png"
    pix.save(outpath)
    print("saved", outpath, pix.width, pix.height)
