"""b8_contact.py PDF FIRST LAST COLS OUT.png [DPI] -- contact sheet of PDF pages (READ-ONLY), page number printed on each tile."""
import sys

import fitz
from PIL import Image, ImageDraw

pdf, a, b, cols, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
dpi = int(sys.argv[6]) if len(sys.argv) > 6 else 45
doc = fitz.open(pdf)
tiles = []
for p in range(a, min(b, len(doc)) + 1):
    pix = doc[p - 1].get_pixmap(dpi=dpi)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 38, 14], fill=(255, 255, 0))
    d.text((2, 1), f"p{p}", fill=(0, 0, 0))
    tiles.append(im)
w = max(t.width for t in tiles)
h = max(t.height for t in tiles)
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h), (255, 255, 255))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * w, (i // cols) * h))
sheet.save(out)
print("saved", out, sheet.size, "tiles", len(tiles))
