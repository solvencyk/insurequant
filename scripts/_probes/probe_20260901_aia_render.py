# -*- coding: utf-8 -*-
from pathlib import Path
import fitz
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
OUT = ROOT / "data" / "_derived" / "item23_children_audit" / "aia_2024q1_pages"
OUT.mkdir(parents=True, exist_ok=True)
pdf_path = list((ROOT/"data"/"disclosure"/"FY2024_Q1"/"raw").glob("KR0080_*.pdf"))[0]
doc = fitz.open(str(pdf_path))
zoom = 240/72
mat = fitz.Matrix(zoom, zoom)
pix = doc[12].get_pixmap(matrix=mat)  # page 13 (0-indexed 12)
pix.save(str(OUT / "p13.png"))
print("saved", OUT/"p13.png")
doc.close()
