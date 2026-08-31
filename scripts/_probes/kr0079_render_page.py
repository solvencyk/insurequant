# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import fitz

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
PDF = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf" / "KR0079_미래에셋생명.pdf"
OUT = ROOT / "scripts" / "_probes" / "kr0079_pages"
OUT.mkdir(parents=True, exist_ok=True)

pages = [int(a) for a in sys.argv[1:]]
dpi = 220
doc = fitz.open(str(PDF))
for p in pages:
    zoom = dpi / 72.0
    pix = doc[p - 1].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    out_path = OUT / f"page_{p}_{dpi}dpi.png"
    pix.save(str(out_path))
    print(f"saved {out_path} {pix.width}x{pix.height}")
doc.close()
