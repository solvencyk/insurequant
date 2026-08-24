# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pdf = ROOT / "data/disclosure/FY2024_Q1/raw/KR1000_코리안리.pdf"
doc = fitz.open(pdf)
page_texts = [doc[i].get_text() for i in range(doc.page_count)]
matched = {i for i, t in enumerate(page_texts) if "공통적용" in t and "보완자본" in t and "한도" in t}
include = set(matched)
for i in matched:
    if i + 1 < len(page_texts):
        include.add(i + 1)
lines = []
for i in sorted(include):
    lines.extend(x.strip() for x in page_texts[i].splitlines())
for idx, l in enumerate(lines):
    print(idx, repr(l))
doc.close()
