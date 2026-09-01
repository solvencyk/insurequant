# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pdf_path = ROOT / "data" / "disclosure" / "FY2024_Q1" / "raw" / "KR0069_삼성생명.pdf"
doc = fitz.open(str(pdf_path))
for pno in (13, 15):
    print(f"===== page {pno} =====")
    print(doc[pno-1].get_text())
    print()
doc.close()
