# -*- coding: utf-8 -*-
"""Read-only: dump every page in KR0003 2026.1Q raw PDF matching the tier2 table keywords,
to see if there are multiple occurrences (current vs prior quarter) and which one the
scanner picked. 2026-08-22 investigation."""
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pdf = ROOT / "data" / "disclosure" / "FY2026_Q1" / "raw" / "KR0003_롯데손해보험.pdf"
doc = fitz.open(pdf)
print(f"pages={doc.page_count}")
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "공통적용" in t and "보완자본" in t and "한도" in t:
        print(f"=== page {i} (0-idx), printed page label maybe {i+1} ===")
        print(t[:2000])
        print("...(truncated)...")
doc.close()
