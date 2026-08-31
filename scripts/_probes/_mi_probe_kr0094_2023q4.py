import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

ROOT = Path(__file__).resolve().parents[2]
p = ROOT / "data" / "disclosure" / "FY2023_Q4" / "raw" / "KR0094_신한라이프생명보험.pdf"
doc = fitz.open(str(p))
print("pages:", len(doc))
for pno in range(min(15, len(doc))):
    t = doc[pno].get_text()
    print(f"--- page {pno + 1} chars={len(t)} ---")
    print(t[:200].replace("\n", " | "))
doc.close()
