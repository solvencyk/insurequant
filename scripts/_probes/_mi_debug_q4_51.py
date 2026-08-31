import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
import fitz

p = REPO / "data" / "disclosure" / "FY2023_Q4" / "raw" / "KR0001_메리츠화재해상보험_amended_amended3.pdf"
doc = fitz.open(str(p))
print("pages:", len(doc))
for pno in range(len(doc)):
    t = doc[pno].get_text().replace(" ", "")
    if "투자이익" in t and "경과운용자산" in t:
        print(f"page {pno+1}:")
        print(doc[pno].get_text()[:600])
        print("---")
doc.close()
