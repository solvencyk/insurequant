"""render_clip.py (parser-kics, ticket 20261012T1030Z) -- READ ONLY.
Find the pages of a PDF that contain an anchor text and/or render a page (or a clip around the anchor) to PNG.
usage:
  render_clip.py PDF --find TEXT                     -> list 1-based pages that contain TEXT (text layer)
  render_clip.py PDF --page N --text                 -> dump the text layer of page N (line by line, y-sorted words)
  render_clip.py PDF --page N --out OUT.png [--dpi 130] [--anchor TEXT --above 220 --below 330]
"""
import io
import sys

import fitz  # PyMuPDF

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
a = sys.argv[1:]
pdf = a[0]
doc = fitz.open(pdf)
print("pdf:", pdf, "| pages:", len(doc))


def arg(name, default=None):
    return a[a.index(name) + 1] if name in a else default


if "--find" in a:
    needle = arg("--find")
    hits = [i + 1 for i, pg in enumerate(doc) if needle in pg.get_text()]
    print("find", repr(needle), "->", hits)
    sys.exit(0)

page_no = int(arg("--page"))
pg = doc[page_no - 1]
if "--text" in a:
    words = pg.get_text("words")  # x0, y0, x1, y1, word, block, line, wordno
    rows = {}
    for w in words:
        rows.setdefault(round(w[1] / 3), []).append(w)
    for k in sorted(rows):
        ws = sorted(rows[k], key=lambda w: w[0])
        print(f"y={ws[0][1]:7.1f} | " + "  ".join(f"{w[4]}" for w in ws))
    sys.exit(0)

out = arg("--out")
dpi = int(arg("--dpi", "130"))
clip = None
anchor = arg("--anchor")
if anchor:
    hits = pg.search_for(anchor)
    print("anchor", repr(anchor), "hits", len(hits), [tuple(round(x, 1) for x in h) for h in hits[:6]])
    if hits:
        h = hits[0]
        above, below = float(arg("--above", "220")), float(arg("--below", "330"))
        clip = fitz.Rect(0, max(0, h.y0 - above), pg.rect.width, min(pg.rect.height, h.y1 + below))
pix = pg.get_pixmap(dpi=dpi, clip=clip)
pix.save(out)
print("saved", out, pix.width, "x", pix.height, "| page rect", pg.rect, "| clip", clip)
