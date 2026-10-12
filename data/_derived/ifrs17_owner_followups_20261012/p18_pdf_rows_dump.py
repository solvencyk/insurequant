# -*- coding: utf-8 -*-
"""Read-only: dump all geometry rows of given pages. Usage: p18 <pdf> <page> [<page> ...]"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts")
import fitz
from bspl_granularity.pdfrows import rows_from_page
doc = fitz.open(sys.argv[1])
for p in sys.argv[2:]:
    rows, free = rows_from_page(doc[int(p) - 1], pageno=int(p))
    print("=" * 100)
    print("PAGE", p, "rows", len(rows))
    for r in rows:
        print(f"   {r.label[:40]:<42s} vals={[int(v) if float(v).is_integer() else v for v in r.vals]} xs={[round(x) for x in r.xs]} y={round(r.y)}")
    print("  free text:", [t[2][:30] for t in free][:40])
