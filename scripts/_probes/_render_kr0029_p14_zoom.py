# -*- coding: utf-8 -*-
import fitz, sys

path = r"data/disclosure/FY2025_Q3/raw/KR0029_AIG손해보험.pdf"
out = r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kr0029_2025q3_p14_full.png"
out_crop = r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kr0029_2025q3_p14_item12_13_zoom.png"

doc = fitz.open(path)
page = doc[13]  # p14, 0-indexed

# full page at 240dpi
zoom = 240 / 72
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat)
pix.save(out)
print("full page saved:", out, pix.width, pix.height)

# crop region around item12/13 rows: y in [100, 350] pdf-pts covers item1 through item13 value rows
clip = fitz.Rect(40, 100, 595, 345)
mat2 = fitz.Matrix(zoom * 2, zoom * 2)  # extra zoom for the crop
pix2 = page.get_pixmap(matrix=mat2, clip=clip)
pix2.save(out_crop)
print("crop saved:", out_crop, pix2.width, pix2.height)
