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
page_idx = emi.find_section_page(doc, ["주요경영지표"], start=0, end=10)
print("1-1 page_idx:", page_idx)
lines = emi.get_page_lines(doc[page_idx])
for i, l in enumerate(lines):
    print(i, repr(l))
doc.close()
