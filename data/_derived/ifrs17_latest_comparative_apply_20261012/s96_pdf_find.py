"""Read-only: find pages of a disclosure PDF that contain a keyword and print the matching lines with a little context.
usage: s96_pdf_find.py <pdf> <keyword-regex> [max_pages] [context]
(PyMuPDF text extraction; page numbers printed are 1-based PDF pages)"""
import re
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")
pdf, pat = sys.argv[1], re.compile(sys.argv[2])
maxp = int(sys.argv[3]) if len(sys.argv) > 3 else 10
ctx = int(sys.argv[4]) if len(sys.argv) > 4 else 2
doc = fitz.open(pdf)
print("pages:", doc.page_count)
hits = 0
for i, page in enumerate(doc):
    lines = page.get_text().splitlines()
    idx = [k for k, l in enumerate(lines) if pat.search(l)]
    if not idx:
        continue
    hits += 1
    print(f"=== p{i + 1}: {len(idx)} matching lines")
    shown = set()
    for k in idx[:6]:
        for j in range(max(0, k - ctx), min(len(lines), k + ctx + 1)):
            if j not in shown:
                shown.add(j)
                print(f"  {j:>4}: {lines[j]}")
        print("  ...")
    if hits >= maxp:
        break
