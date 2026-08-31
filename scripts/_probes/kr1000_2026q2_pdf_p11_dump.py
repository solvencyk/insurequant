import fitz, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

doc = fitz.open("data/disclosure/FY2026_Q2/pdf/KR1000_코리안리재보험.pdf")
page = doc[10]  # p11, 0-indexed
print(page.get_text())
