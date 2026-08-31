#!/usr/bin/env python3
"""Render a contact sheet of candidate pages from KB손해보험 2026.2Q raw PDF to locate
the 6-8-2) 금리 민감도 분석 table visually (page has 0 native text -- scan/OCR only)."""
from __future__ import annotations

import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
pdf_path = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf" / "KR0010_KB손해보험.pdf"
OUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scripts" / "_probes"

doc = fitz.open(pdf_path)

# render pages 40..51 (0-idx 39..50) at modest zoom for a contact sheet
lo, hi = 39, 51
zoom = 1.2
mat = fitz.Matrix(zoom, zoom)
imgs = []
for i in range(lo, hi):
    pix = doc[i].get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    imgs.append((i + 1, img))

cols = 4
rows = (len(imgs) + cols - 1) // cols
w, h = imgs[0][1].size
sheet = Image.new("RGB", (w * cols, h * rows), "white")
from PIL import ImageDraw
for idx, (pno, img) in enumerate(imgs):
    r, c = divmod(idx, cols)
    sheet.paste(img, (c * w, r * h))
    d = ImageDraw.Draw(sheet)
    d.rectangle([c * w, r * h, c * w + 60, r * h + 22], fill="yellow")
    d.text((c * w + 4, r * h + 4), f"p{pno}", fill="black")

out_path = OUT_DIR / "kb_contact_sheet_40_51.png"
sheet.save(out_path)
print(f"wrote {out_path}  size={sheet.size}")
