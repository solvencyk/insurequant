# -*- coding: utf-8 -*-
import fitz, sys, os

pdf_path = r"data\disclosure\FY2026_Q2\pdf\KR0010_KB손해보험.pdf"
out_dir = r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kr0010_pages"
os.makedirs(out_dir, exist_ok=True)

pages = [int(p) for p in sys.argv[1:]]
doc = fitz.open(pdf_path)
print("doc page count:", doc.page_count)
zoom = 220/72.0
mat = fitz.Matrix(zoom, zoom)
for p in pages:
    idx = p - 1
    if idx < 0 or idx >= doc.page_count:
        print(f"page {p} out of range")
        continue
    pix = doc[idx].get_pixmap(matrix=mat)
    out_path = os.path.join(out_dir, f"p{p:02d}.png")
    pix.save(out_path)
    print(f"saved page {p} -> {out_path} ({pix.width}x{pix.height})")
