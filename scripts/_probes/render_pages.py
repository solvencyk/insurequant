# -*- coding: utf-8 -*-
"""Read-only: render a page range of a raw disclosure PDF to a single stitched
PNG (vertical concat) for visual inspection via the Read tool, when the PDF has
no usable text layer (scanned). Writes only to --out (scratchpad).

Usage:
  python scripts/_probes/render_pages.py --code KR0080 --period FY2025_Q1 --pages 12-22 --out OUT.png [--dpi 150]
"""
import argparse
import glob
import sys
import fitz
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True)
    ap.add_argument("--period", required=True)
    ap.add_argument("--pages", required=True, help="1-based inclusive range, e.g. 12-22, or single 'N'")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dpi", type=int, default=150)
    args = ap.parse_args()

    if "-" in args.pages:
        lo, hi = (int(x) for x in args.pages.split("-"))
    else:
        lo = hi = int(args.pages)

    pdfs = sorted(glob.glob(f"data/disclosure/{args.period}/raw/{args.code}_*.pdf"))
    if not pdfs:
        print("NO PDF FOUND")
        return
    doc = fitz.open(pdfs[-1])
    print(f"pdf={pdfs[-1]} pages_total={doc.page_count}")
    lo = max(1, lo)
    hi = min(doc.page_count, hi)
    imgs = []
    for p in range(lo, hi + 1):
        pix = doc[p - 1].get_pixmap(dpi=args.dpi)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        imgs.append((p, img))
    total_h = sum(im.height for _, im in imgs) + 24 * len(imgs)
    max_w = max(im.width for _, im in imgs)
    canvas = Image.new("RGB", (max_w, total_h), "white")
    y = 0
    from PIL import ImageDraw
    draw = ImageDraw.Draw(canvas)
    for p, im in imgs:
        draw.text((5, y + 2), f"page {p}", fill=(255, 0, 0))
        canvas.paste(im, (0, y + 20))
        y += im.height + 24
    canvas.save(args.out)
    print(f"wrote {args.out} size={canvas.size}")
    doc.close()


if __name__ == "__main__":
    main()
