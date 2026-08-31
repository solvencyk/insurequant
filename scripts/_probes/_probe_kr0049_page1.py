import fitz
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = "data/disclosure/FY2026_Q2/pdf/KR0049_악사손해보험.pdf"
doc = fitz.open(PDF)
print(doc[0].get_text())
