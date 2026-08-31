import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

p = Path("data/disclosure/FY2026_Q2/pdf/KR0004_MG_예별손해보험.pdf")
doc = fitz.open(str(p))
print(f"pages={doc.page_count}")
for i, page in enumerate(doc):
    text = page.get_text()
    if "경과조치" in text or "보완자본" in text:
        print(f"--- page {i+1} (has 경과조치 or 보완자본) ---")
        print(text[:1500])
        print("...")
doc.close()
