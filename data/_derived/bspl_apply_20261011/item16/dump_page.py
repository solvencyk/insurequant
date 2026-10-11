import sys, fitz
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
fy, code, p = sys.argv[1], sys.argv[2], int(sys.argv[3])
for f in sorted((Path("data/disclosure")/fy/"raw").glob(f"{code}_*.pdf")):
    d = fitz.open(str(f))
    print("=====", f.name, "pages", len(d), "page", p)
    t = d[p-1].get_text("text")
    print(t[:int(sys.argv[4]) if len(sys.argv)>4 else 4000])
