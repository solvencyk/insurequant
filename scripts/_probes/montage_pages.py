# -*- coding: utf-8 -*-
"""PDF 페이지 범위를 썸네일 몽타주(그리드) 1장으로 합성 -- 후보 페이지 빠른 스캔용.
Usage: montage_pages.py <pdf_path> <page0_start> <page0_end_inclusive> <out_png> [cols] [thumb_w]
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


def main():
    pdf_path = Path(sys.argv[1])
    p0 = int(sys.argv[2])
    p1 = int(sys.argv[3])
    out = Path(sys.argv[4])
    cols = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    thumb_w = int(sys.argv[6]) if len(sys.argv) > 6 else 500

    doc = fitz.open(pdf_path)
    pages = list(range(p0, min(p1 + 1, doc.page_count)))
    thumbs = []
    for p in pages:
        pg = doc[p]
        rect = pg.rect
        zoom = thumb_w / rect.width
        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        # label bar
        bar_h = 28
        canvas = Image.new("RGB", (img.width, img.height + bar_h), "white")
        canvas.paste(img, (0, bar_h))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, 0, img.width, bar_h], fill=(20, 20, 20))
        draw.text((6, 6), f"page0={p} (printed~{p+1})", fill="yellow")
        thumbs.append(canvas)
    doc.close()

    if not thumbs:
        print("no pages")
        return

    tw, th = thumbs[0].size
    rows = (len(thumbs) + cols - 1) // cols
    grid = Image.new("RGB", (tw * cols, th * rows), "white")
    for i, im in enumerate(thumbs):
        r, c = divmod(i, cols)
        grid.paste(im, (c * tw, r * th))

    out.parent.mkdir(parents=True, exist_ok=True)
    grid.save(out)
    print(f"wrote {out}  ({len(thumbs)} pages, {cols} cols x {rows} rows, tile={tw}x{th})")


if __name__ == "__main__":
    main()
