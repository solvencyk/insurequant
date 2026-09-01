# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import fitz
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
OUT = ROOT / "data" / "_derived" / "item23_children_audit" / "kakaopay_2024q4_pages"
OUT.mkdir(parents=True, exist_ok=True)
pdf_path = ROOT / "data" / "disclosure" / "FY2024_Q4" / "raw" / "KR1098_카카오페이손해보험.pdf"
doc = fitz.open(str(pdf_path))
zoom = 240 / 72
mat = fitz.Matrix(zoom, zoom)
for pno in [27, 28, 29, 30, 31, 32]:  # 0-indexed -> pages 28-33
    pix = doc[pno].get_pixmap(matrix=mat)
    out_path = OUT / f"p{pno+1}.png"
    pix.save(str(out_path))
    print(f"saved {out_path}")
doc.close()
