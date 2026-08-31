import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import extract_management_indicators as emi
import fitz

p = REPO / "data" / "disclosure" / "FY2024_Q4" / "raw" / "KR0069_삼성생명.pdf"
doc = fitz.open(str(p))
page_idx = emi.find_section_page(doc, ["투자이익", "경과운용자산"], start=2, end=200, min_numeric=4, require_short_labels=True)
print("found at:", page_idx + 1 if page_idx is not None else None)
if page_idx is not None:
    print(doc[page_idx].get_text()[:500])
doc.close()
