# -*- coding: utf-8 -*-
"""KR0069 2024.1Q raw PDF 전체 페이지에서 시장위험 세부표(항목36-40) 존재여부 직접 확인.
case (c) genuine absence 인지, case (b) docling window drop 인지 판별."""
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pdf_path = ROOT / "data" / "disclosure" / "FY2024_Q1" / "raw" / "KR0069_삼성생명.pdf"
doc = fitz.open(str(pdf_path))
print(f"total pages: {doc.page_count}")

kws = ["금리위험액", "주식위험액", "부동산위험액", "외환위험액", "자산집중위험액", "시장위험액", "순자산가치"]
for i in range(doc.page_count):
    t = doc[i].get_text()
    hits = {kw: t.count(kw) for kw in kws if kw in t}
    if hits:
        print(f"p{i+1} ({len(t)} chars): {hits}")
doc.close()
