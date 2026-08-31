import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
import fitz

p = REPO / "data" / "disclosure" / "FY2024_Q4" / "raw" / "KR0069_삼성생명.pdf"
doc = fitz.open(str(p))
print("pages:", len(doc))
for pno in range(len(doc)):
    t = doc[pno].get_text().replace(" ", "")
    if "투자이익" in t and "경과운용자산" in t:
        print(f"page {pno + 1}")
        print(doc[pno].get_text()[:400])
        break
doc.close()
