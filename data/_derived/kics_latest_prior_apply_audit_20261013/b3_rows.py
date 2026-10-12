import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_pdf import *
import fitz
here = os.path.dirname(os.path.abspath(__file__))
pdf, pages, outp = sys.argv[1], sys.argv[2], sys.argv[3]
doc = fitz.open(pdf)
with open(here + "/" + outp, "w", encoding="utf-8") as f:
    for p in [int(x) for x in pages.split(",")]:
        f.write(f"######## {os.path.basename(pdf)} p{p}\n")
        for y, ws in page_rows(doc, p):
            f.write(f"{y:6.1f} | " + " ".join(t for _, _, t in ws) + "\n")
