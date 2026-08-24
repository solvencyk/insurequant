# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pdf = ROOT / "data/disclosure/FY2026_Q1/raw/KR0087_동양생명.pdf"
doc = fitz.open(pdf)
print("pages:", doc.page_count)
toc = doc.get_toc()
print("toc:", toc)
for i in range(doc.page_count):
    t = doc[i].get_text()
    print(i, len(t), repr(t[:60]))
doc.close()
