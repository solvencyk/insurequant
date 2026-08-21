"""Render specific PDF pages to PNG at given DPI for visual inspection (image-only PDFs).
Usage: python render_pages_20260821.py <pdf_path> <out_dir> <dpi> <page1> [page2 ...]
Page numbers are 1-indexed.
"""
import sys
import io
import fitz
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main():
    pdf_path = sys.argv[1]
    out_dir = Path(sys.argv[2])
    dpi = int(sys.argv[3])
    pages = [int(p) for p in sys.argv[4:]]
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    for p in pages:
        idx = p - 1
        if idx < 0 or idx >= doc.page_count:
            print(f"page {p} out of range")
            continue
        pix = doc[idx].get_pixmap(matrix=mat)
        out_path = out_dir / f"p{p:03d}.png"
        pix.save(str(out_path))
        print(f"saved {out_path} ({pix.width}x{pix.height})")


if __name__ == "__main__":
    main()
