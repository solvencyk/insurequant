import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
from lib_pdf import page_rows
here = os.path.dirname(os.path.abspath(__file__))
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
out = open(here + "/h6_kr0075.txt", "w", encoding="utf-8")
pdf = REPO + "/data/disclosure/FY2023_Q1/raw/KR0075_비엔피파리바카디프생명보험.pdf"
doc = fitz.open(pdf)
for pn in range(1, len(doc) + 1):
    flat = re.sub(r"\s+", "", doc[pn - 1].get_text())
    if re.search(r"포괄손익계산서|손익계산서", flat) and "영업" in flat:
        out.write(f"p{pn}: chars={len(flat)} {flat[:200]}\n")
