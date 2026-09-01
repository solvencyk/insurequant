# -*- coding: utf-8 -*-
"""Read-only probe: inspect raw PDF pages 25-34 of KR0069 2026.2Q via fitz.
Checks text density (scanned vs text-layer) and presence of 금리위험액/주식위험액 headers.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
pdf_path = REPO / "data" / "disclosure" / "FY2026_Q2" / "pdf" / "KR0069_삼성생명.pdf"
print(f"pdf: {pdf_path}  exists={pdf_path.exists()}")
doc = fitz.open(pdf_path)
print(f"total pages: {doc.page_count}")

for i in range(24, 35):  # 0-based -> pages 25..35
    if i >= doc.page_count:
        break
    page = doc[i]
    text = page.get_text()
    density = len(text)
    hits = [kw for kw in ("금리위험액", "주식위험액", "부동산위험액", "외환위험액", "자산집중위험액",
                           "순자산가치", "6-4", "시장위험") if kw in text]
    first_line = text.strip().splitlines()[0] if text.strip() else "(empty)"
    print(f"page {i+1:>3}  chars={density:>6}  hits={hits}  first_line={first_line[:60]!r}")

print("\n--- full text of pages 29-32 (1-based) ---")
for pno in (29, 30, 31, 32):
    idx = pno - 1
    if idx >= doc.page_count:
        continue
    print(f"\n===== PAGE {pno} =====")
    print(doc[idx].get_text())

doc.close()
