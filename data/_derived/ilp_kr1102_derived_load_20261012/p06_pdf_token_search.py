# -*- coding: utf-8 -*-
"""Read-only: search every page of the KR1102 FY2026_Q1 PDF for tokens that would independently anchor the all-row sums,
and list pages mentioning 보험계약마진 / 잔여보장 / 합계 (text layer, PyMuPDF)."""
import re, sys
sys.stdout.reconfigure(encoding="utf-8")
import fitz
PDF = "C:/Users/sangwook.cho/Desktop/insurequant/data/disclosure/FY2026_Q1/raw/KR1102_스위스리아시아.pdf"
doc = fitz.open(PDF)
tokens = ["12,221", "9,227", "2,200", "2,201", "7,506", "4,715", "1,403", "(794", "794"]
for i, pg in enumerate(doc, start=1):
    t = pg.get_text("text", sort=True)
    flat = re.sub(r"\s+", "", t)
    hits = [k for k in tokens if k in t or k.replace(",", "") in flat]
    kw = [k for k in ("보험계약마진", "잔여보장", "Indirect", "Non-Par", "무저해지", "해지율") if k in flat or k in t]
    print(f"p{i:02d} hits={hits} kw={kw}")
