# -*- coding: utf-8 -*-
"""Dump text of specific low-char pages for context (0-idx list below)."""
import json
from pathlib import Path

import fitz

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2024_Q4\raw\KR0005_흥국화재.pdf")
OUT = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\c9c7c053-f96a-4878-bcb0-5ff8567de9fd\scratchpad\kr0005_tfi")

doc = fitz.open(PDF)
pages_0idx = [20, 22, 35, 44, 53, 86, 89]
out = {}
for i in pages_0idx:
    out[str(i)] = {"page_1idx": i + 1, "text": doc[i].get_text()}

(OUT / "smallpages.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", OUT / "smallpages.json")
