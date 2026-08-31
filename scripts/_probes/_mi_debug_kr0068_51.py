import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import extract_management_indicators as emi
import fitz

p = REPO / "data/disclosure/FY2026_Q2/pdf/KR0068_한화생명.pdf"
doc = fitz.open(str(p))
page_idx = emi.find_section_page(doc, ["투자이익", "경과운용자산"], start=2, end=35, min_numeric=4, require_short_labels=True)
print("5-1 page_idx:", page_idx)
if page_idx is not None:
    lines = emi.get_page_lines(doc[page_idx])
    for i, l in enumerate(lines):
        print(i, repr(l))
