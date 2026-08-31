import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
import fitz

for stem in ["KR0068_한화생명", "KR0069_삼성생명", "KR0094_신한라이프생명보험"]:
    p = REPO / "data" / "disclosure" / "FY2024_Q4" / "raw" / f"{stem}.pdf"
    if not p.exists():
        print(stem, "NOT FOUND")
        continue
    doc = fitz.open(str(p))
    print(f"\n=== {stem} ===")
    for pno in range(min(6, len(doc))):
        t = doc[pno].get_text().replace(" ", "")
        if "주요경영지표" in t:
            print(f"page {pno+1}:")
            print(doc[pno].get_text()[:500])
            break
    doc.close()
