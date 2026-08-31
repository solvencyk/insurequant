import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
import fitz

p = REPO / "data" / "disclosure" / "FY2023_Q4" / "raw" / "KR0001_메리츠화재해상보험_amended_amended3.pdf"
doc = fitz.open(str(p))
print(doc[2].get_text()[:800])
doc.close()
