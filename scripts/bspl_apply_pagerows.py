# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, "scripts")
import fitz
from bspl_granularity.pdfrows import rows_from_page
sys.stdout.reconfigure(encoding="utf-8")
fy, code, pages = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(",")]
f = sorted((Path("data/disclosure") / fy / "raw").glob(f"{code}_*.pdf"))[0]
doc = fitz.open(str(f))
for p in pages:
    rows, free = rows_from_page(doc[p - 1], pageno=p)
    print("=== page", p, f.name)
    for r in rows:
        print(f"  {r.label[:40]:<40} {list(r.vals)}")
    for y, x, t in free[:0]:
        print("   free:", t)
