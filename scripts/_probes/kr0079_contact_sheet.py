# -*- coding: utf-8 -*-
"""Render KR0079 2026.2Q PDF pages into contact-sheet composites for fast visual scanning."""
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
PDF = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf" / "KR0079_미래에셋생명.pdf"
OUT = ROOT / "scripts" / "_probes" / "kr0079_pages"
OUT.mkdir(parents=True, exist_ok=True)

def render_contact_sheet(start_page, end_page, cols=4, thumb_w=380, dpi=110, tag=""):
    doc = fitz.open(str(PDF))
    pages = list(range(start_page, min(end_page, doc.page_count) + 1))
    rows = (len(pages) + cols - 1) // cols
    zoom = dpi / 72.0
    thumbs = []
    for p in pages:
        pix = doc[p - 1].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        ratio = thumb_w / img.width
        img = img.resize((thumb_w, int(img.height * ratio)))
        thumbs.append((p, img))
    th = max(im.height for _, im in thumbs)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (th + 24)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (p, im) in enumerate(thumbs):
        r, c = divmod(idx, cols)
        x, y = c * thumb_w, r * (th + 24)
        sheet.paste(im, (x, y + 20))
        draw.text((x + 4, y + 2), f"p{p}", fill="red")
    out_path = OUT / f"contact_{tag}{start_page}_{end_page}.png"
    sheet.save(out_path)
    print(f"saved {out_path} ({len(pages)} pages, {sheet.width}x{sheet.height})")
    doc.close()

if __name__ == "__main__":
    ranges = [(1, 20), (21, 40), (41, 65)]
    for a, b in ranges:
        render_contact_sheet(a, b)
