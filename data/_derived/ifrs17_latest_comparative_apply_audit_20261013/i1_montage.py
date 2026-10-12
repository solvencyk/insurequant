import sys, os, fitz
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__))
pdf, pages, outp = sys.argv[1], [int(x) for x in sys.argv[2].split(",")], sys.argv[3]
doc = fitz.open(pdf)
ims = []
for p in pages:
    pix = doc[p - 1].get_pixmap(matrix=fitz.Matrix(float(os.environ.get("MSC","0.6")), float(os.environ.get("MSC","0.6"))))
    ims.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
w = sum(i.width for i in ims); h = max(i.height for i in ims)
m = Image.new("RGB", (w, h), "white"); x = 0
for i in ims: m.paste(i, (x, 0)); x += i.width
m.save(outp)
print(m.size)
