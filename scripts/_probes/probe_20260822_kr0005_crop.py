# -*- coding: utf-8 -*-
"""Crop the (1) 공통적용 경과조치 table region out of the dpi280 render of p41."""
from pathlib import Path
from PIL import Image

OUT = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\c9c7c053-f96a-4878-bcb0-5ff8567de9fd\scratchpad\kr0005_tfi")
img = Image.open(OUT / "p041_1idx_dpi280.png")
w, h = img.size
print("full size", w, h)
# table roughly top ~14% to ~48% vertically based on the 150dpi preview proportions
crop = img.crop((0, int(h * 0.10), w, int(h * 0.50)))
crop.save(OUT / "p041_table_crop.png")
print("cropped size", crop.size)
