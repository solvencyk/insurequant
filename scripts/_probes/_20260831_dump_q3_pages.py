# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
pdf = fitz.open(ROOT / "data/disclosure/FY2023_Q3/raw/KR0029_AIG손해보험.pdf")
for pno in (8, 9, 10):  # 0-indexed pages 9,10,11
    print(f"\n=====PAGE {pno+1}=====")
    print(pdf[pno].get_text())
