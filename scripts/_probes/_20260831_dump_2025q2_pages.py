# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
pdf = fitz.open(ROOT / "data/disclosure/FY2025_Q2/raw/KR0029_AIG손해보험.pdf")
for pno in (19, 20, 28):  # 0-idx for pages 20,21,29
    print(f"\n=====PAGE {pno+1}=====")
    print(pdf[pno].get_text())
