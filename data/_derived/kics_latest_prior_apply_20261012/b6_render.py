"""b6_render.py PDF PAGE OUT.png [DPI] [x0,y0,x1,y1]  -- render one PDF page (1-based) to PNG (READ-ONLY on the PDF).
Clip is in PDF points (page.rect units).  Prints the page size so a clip can be chosen."""
import sys

import fitz

pdf, page_no, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 130
clip = None
if len(sys.argv) > 5:
    x0, y0, x1, y1 = [float(x) for x in sys.argv[5].split(",")]
    clip = fitz.Rect(x0, y0, x1, y1)
doc = fitz.open(pdf)
page = doc[page_no - 1]
print("page rect", page.rect, "rotation", page.rotation)
pix = page.get_pixmap(dpi=dpi, clip=clip)
pix.save(out)
print("saved", out, pix.width, "x", pix.height)
