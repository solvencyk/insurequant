"""Dump text of given pages (1-based) of a raw PDF into pages_text/<stem>_pN.txt. Usage: dump_pages.py <pdf relative path> p1,p2,..."""
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "pages_text"
OUT.mkdir(exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
pdf = ROOT / sys.argv[1]
doc = fitz.open(str(pdf))
for p in [int(x) for x in sys.argv[2].split(",")]:
    t = doc[p - 1].get_text("text")
    fn = OUT / f"{pdf.stem}_{pdf.parent.parent.name}_p{p}.txt"
    fn.write_text(t, encoding="utf-8")
    print(fn.name, len(t))
