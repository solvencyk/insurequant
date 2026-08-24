# -*- coding: utf-8 -*-
"""
Render specific 0-idx pages of KR0005 FY2024_Q4 raw PDF to PNG for vision inspection.
Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260822_kr0005_render.py <dpi> <page0> <page1> ...
"""
import sys
from pathlib import Path

import fitz

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2024_Q4\raw\KR0005_흥국화재.pdf")
OUT = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\c9c7c053-f96a-4878-bcb0-5ff8567de9fd\scratchpad\kr0005_tfi")
OUT.mkdir(parents=True, exist_ok=True)

args = sys.argv[1:]
dpi = int(args[0])
pages_0idx = [int(a) for a in args[1:]]

doc = fitz.open(PDF)
for i in pages_0idx:
    if i < 0 or i >= doc.page_count:
        print(f"skip out-of-range 0idx={i}")
        continue
    pix = doc[i].get_pixmap(dpi=dpi)
    out_path = OUT / f"p{i+1:03d}_1idx_dpi{dpi}.png"
    pix.save(str(out_path))
    print(f"wrote {out_path} ({pix.width}x{pix.height})")

doc.close()
