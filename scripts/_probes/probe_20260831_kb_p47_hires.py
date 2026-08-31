#!/usr/bin/env python3
"""Render KB손해보험 2026.2Q raw PDF page 47 (금리 민감도 분석 table) at high DPI."""
from __future__ import annotations
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
pdf_path = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf" / "KR0010_KB손해보험.pdf"
doc = fitz.open(pdf_path)
page = doc[46]  # page 47, 0-idx 46
zoom = 4.0
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat)
out = Path(__file__).resolve().parent / "kb_p47_hires.png"
pix.save(str(out))
print(f"wrote {out} size={pix.width}x{pix.height}")

# also crop to just the table region (roughly lower-right quadrant based on contact sheet)
# full page rect
r = page.rect
print(f"page rect: {r}")
