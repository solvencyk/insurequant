# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pdf = ROOT / "data" / "disclosure" / "FY2026_Q1" / "raw" / "KR0003_롯데손해보험.pdf"
doc = fitz.open(pdf)
for i in [21, 22]:
    print(f"=========== page idx {i} (printed {i+1}) FULL ===========")
    print(doc[i].get_text())
doc.close()
