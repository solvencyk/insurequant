#!/usr/bin/env python3
"""Crop + zoom just the 금리 민감도 table region on KB손해보험 2026.2Q p47."""
from __future__ import annotations
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
pdf_path = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf" / "KR0010_KB손해보험.pdf"
doc = fitz.open(pdf_path)
page = doc[46]  # page 47, 0-idx 46

zoom = 6.0
mat = fitz.Matrix(zoom, zoom)
clip = fitz.Rect(0, 230, 595.32, 420)  # table region guess
pix = page.get_pixmap(matrix=mat, clip=clip)
out = Path(__file__).resolve().parent / "kb_p47_crop.png"
pix.save(str(out))
print(f"wrote {out} size={pix.width}x{pix.height}")
