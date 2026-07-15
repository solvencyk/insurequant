"""Render candidate pages of the scanned-image 흥국생명 FY2024_Q4 PDF to PNG
for vision reading (internal page numbers ~44-50 per the 2026-07-07(8차)
changelog precedent that recovered items 1-3/14/27/28 from this same doc)."""
import sys
from pathlib import Path

import fitz

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
OUT = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\dc9fd245-4fdc-4fb9-ae5d-21d82eadad07\scratchpad")
OUT.mkdir(parents=True, exist_ok=True)

doc = fitz.open(REPO / "data/disclosure/FY2024_Q4/raw/KR0071_흥국생명보험.pdf")
# try absolute PDF pages 44-52 (offset unknown, scan for the right one first with low-res)
for p in range(43, 53):
    page = doc[p]
    pix = page.get_pixmap(dpi=100)
    out_path = OUT / f"hkl_p{p+1}.png"
    pix.save(str(out_path))
    print(f"saved {out_path}")
doc.close()
