import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import extract_management_indicators as emi
import fitz

p = REPO / "data" / "disclosure" / "FY2026_Q2" / "pdf" / "KR0001_메리츠화재해상보험.pdf"
doc = fitz.open(str(p))
page_idx = emi.find_section_page(doc, ["투자이익", "경과운용자산"], start=2, end=35, min_numeric=4)
print("page_idx:", page_idx)
if page_idx is not None:
    print(doc[page_idx].get_text()[:1200])
else:
    # scan pages 2-35 manually for the keywords
    for pno in range(2, min(35, len(doc))):
        t = doc[pno].get_text().replace(" ", "")
        if "투자이익" in t and "경과운용자산" in t:
            print(f"page {pno+1} has both keywords, raw text:")
            print(doc[pno].get_text()[:800])
