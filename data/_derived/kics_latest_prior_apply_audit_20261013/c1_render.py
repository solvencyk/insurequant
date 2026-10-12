import sys, fitz
pdf, pno, outp = sys.argv[1], int(sys.argv[2]), sys.argv[3]
clip = None
if len(sys.argv) > 4:
    x0, y0, x1, y1 = [float(v) for v in sys.argv[4].split(",")]   # fractions of page
    clip = "frac"
doc = fitz.open(pdf)
pg = doc[pno - 1]
r = pg.rect
if clip:
    rect = fitz.Rect(r.x0 + x0 * r.width, r.y0 + y0 * r.height, r.x0 + x1 * r.width, r.y0 + y1 * r.height)
    pix = pg.get_pixmap(matrix=fitz.Matrix(240/72, 240/72), clip=rect)
else:
    pix = pg.get_pixmap(matrix=fitz.Matrix(240/72, 240/72))
pix.save(outp)
print(pix.width, pix.height)
