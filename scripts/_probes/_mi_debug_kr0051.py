import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
import fitz

p = REPO / "data/disclosure/FY2026_Q2/pdf/KR0051_신한이지손해보험.pdf"
doc = fitz.open(str(p))
lines = doc[2].get_text().splitlines()
for i, l in enumerate(lines):
    print(i, repr(l))
doc.close()
