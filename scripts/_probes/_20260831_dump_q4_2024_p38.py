# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
pdf = fitz.open(ROOT / "data/disclosure/FY2024_Q4/raw/KR0029_AIG손해보험.pdf")
print(pdf[37].get_text())  # page 38, 0-indexed 37
