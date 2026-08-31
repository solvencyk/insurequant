import fitz
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = "data/disclosure/FY2026_Q2/pdf/KR0049_악사손해보험.pdf"
doc = fitz.open(PDF)

for pno in [35, 36, 37, 38, 39, 40]:
    page = doc[pno - 1]
    print(f"\n{'='*20} PAGE {pno} {'='*20}")
    print(page.get_text())
