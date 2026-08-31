import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
import fitz

p = REPO / "data" / "disclosure" / "FY2023_Q1" / "raw" / "KR0001_메리츠화재해상보험.pdf"
doc = fitz.open(str(p))
found = False
for pno in range(len(doc)):
    t = doc[pno].get_text().replace(" ", "")
    if "경영효율지표" in t or "신계약률" in t:
        print(f"page {pno+1}: HIT")
        print(doc[pno].get_text()[:400])
        found = True
print("found anywhere:", found, "total pages:", len(doc))
doc.close()
