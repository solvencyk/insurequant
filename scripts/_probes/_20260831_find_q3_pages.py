# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
pdf = fitz.open(ROOT / "data/disclosure/FY2023_Q3/raw/KR0029_AIG손해보험.pdf")
print(f"total pages: {pdf.page_count}")
for i in range(pdf.page_count):
    text = pdf[i].get_text()
    if "지급여력비율 세부" in text or "경과조치 적용 전" in text or "보통주" in text and "이익잉여금" in text:
        print(f"--- page {i+1} (0-idx {i}) has relevant keywords ---")
        print(f"  len={len(text)}, first 100 chars: {text[:100]!r}")
