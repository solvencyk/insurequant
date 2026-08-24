# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pdf = ROOT / "data" / "disclosure" / "FY2025_Q4" / "raw" / "KR0003_롯데손해보험.pdf"
doc = fitz.open(pdf)
print(f"pages={doc.page_count}")
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "공통적용" in t and "보완자본" in t and "한도" in t:
        print(f"=== page idx {i} (printed {i+1}) ===")
        print(t)
doc.close()
