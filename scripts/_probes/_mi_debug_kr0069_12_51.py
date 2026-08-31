import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import extract_management_indicators as emi
import fitz

p = REPO / "data/disclosure/FY2026_Q2/pdf/KR0069_삼성생명.pdf"
doc = fitz.open(str(p))
p12 = emi.find_section_page(doc, ["주요경영효율지표"], start=0, end=10)
print("1-2 page_idx:", p12)
lines = emi.get_page_lines(doc[p12])
for i, l in enumerate(lines):
    print(i, repr(l))
print("direction:", emi.detect_layout_direction(lines, sample_labels=("신계약률", "보험금지급률", "자산운용률")))

p51 = emi.find_section_page(doc, ["투자이익", "경과운용자산"], start=2, end=35, min_numeric=4, require_short_labels=True)
print("\n5-1 page_idx:", p51)
lines51 = emi.get_page_lines(doc[p51])
for i, l in enumerate(lines51):
    print(i, repr(l))
print("direction:", emi.detect_layout_direction(lines51, sample_labels=("투자이익", "경과운용자산")))
doc.close()
