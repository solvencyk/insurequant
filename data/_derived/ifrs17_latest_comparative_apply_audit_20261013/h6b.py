import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
from lib_pdf import page_rows
here = os.path.dirname(os.path.abspath(__file__))
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
out = open(here + "/h6b.txt", "w", encoding="utf-8")
for fq, pn in (("FY2023_Q1", 4), ("FY2024_Q1", 4)):
    pdf = REPO + f"/data/disclosure/{fq}/raw/KR0075_비엔피파리바카디프생명보험" + ("_amended" if fq == "FY2024_Q1" else "") + ".pdf"
    doc = fitz.open(pdf)
    out.write(f"#### {fq} p{pn}\n")
    for y, ws in page_rows(doc, pn):
        out.write(f"{y:6.1f} | " + " ".join(t for _, _, t in ws)[:170] + "\n")
