import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_kics import *
pdf = sys.argv[1]; lo, hi = int(sys.argv[2]), int(sys.argv[3])
doc = fitz.open(pdf)
out = open(os.path.dirname(os.path.abspath(__file__)) + "/a7_scan_titles.txt", "w", encoding="utf-8")
for p in range(lo, min(hi, len(doc)) + 1):
    txt = doc[p-1].get_text()
    flat = re.sub(r"\s+", "", txt)
    out.write(f"p{p} chars={len(txt)} :: {flat[:160]}\n")
