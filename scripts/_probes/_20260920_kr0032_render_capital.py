"""Render the KR0032 capital-component table region at 240dpi.

Guards against a lying text layer (bad font CMap / scanned page): we read the
values out of the text layer, so we must SEE the same glyphs.
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "artifacts", "kr0032_render")
os.makedirs(OUT, exist_ok=True)

# (label, pdf, 0-based page, clip rect in PDF points)
JOBS = [
    ("2023.2Q_p11", "data/disclosure/FY2023_Q2/raw/KR0032_NH농협손해보험_amended.pdf", 10,
     fitz.Rect(40, 415, 560, 760)),
    ("2023.3Q_p10", "data/disclosure/FY2023_Q3/raw/KR0032_NH농협손해보험_amended.pdf", 9,
     fitz.Rect(40, 425, 560, 760)),
    ("2024.4Q_p43", "data/disclosure/FY2024_Q4/raw/KR0032_NH농협손해보험.pdf", 42,
     fitz.Rect(40, 80, 560, 410)),
    ("2024.4Q_p42", "data/disclosure/FY2024_Q4/raw/KR0032_NH농협손해보험.pdf", 41,
     fitz.Rect(40, 85, 560, 270)),
]

ZOOM = 240 / 72.0
for tag, rel, pno, clip in JOBS:
    path = os.path.join(ROOT, rel)
    doc = fitz.open(path)
    page = doc[pno]
    pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip)
    dst = os.path.join(OUT, f"{tag}.png")
    pix.save(dst)
    print(f"{tag}: {dst}  {pix.width}x{pix.height}  page_rect={page.rect}  "
          f"images_on_page={len(page.get_images(full=True))}  textlen={len(page.get_text('text'))}")
    doc.close()
