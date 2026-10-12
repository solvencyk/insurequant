# -*- coding: utf-8 -*-
"""Read-only: Chubb mid-quarter balance-sheet rows (geometry rebuild via scripts/bspl_granularity/pdfrows.rows_from_page).
Prints, for every page that carries the liabilities block (부채총계 + 보험계약부채 rows), the rows whose label matches the filter, with x positions.
Usage: p17 <quarter> [<quarter> ...]"""
import re, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts")
import fitz
from bspl_granularity.pdfrows import rows_from_page
R = "C:/Users/sangwook.cho/Desktop/insurequant/data/disclosure/"
PDF = {
    "2023.1Q": R + "FY2023_Q1/raw/KR0100_처브라이프생명보험.pdf",
    "2023.2Q": R + "FY2023_Q2/raw/KR0100_처브라이프생명보험.pdf",
    "2023.3Q": R + "FY2023_Q3/raw/KR0100_처브라이프생명보험.pdf",
    "2024.1Q": R + "FY2024_Q1/raw/KR0100_처브라이프생명보험_amended.pdf",
    "2024.2Q": R + "FY2024_Q2/raw/KR0100_처브라이프생명보험.pdf",
    "2024.3Q": R + "FY2024_Q3/raw/KR0100_처브라이프생명보험_amended.pdf",
    "2025.1Q": R + "FY2025_Q1/raw/KR0100_처브라이프생명보험.pdf",
    "2025.2Q": R + "FY2025_Q2/raw/KR0100_처브라이프생명보험.pdf",
    "2025.3Q": R + "FY2025_Q3/raw/KR0100_처브라이프생명보험.pdf",
}
KEY = ("보험계약부채", "특별계정부채", "부채총계", "잔여보장요소", "발생사고요소", "책임준비금", "재보험계약부채")
for q in sys.argv[1:]:
    doc = fitz.open(PDF[q])
    print("=" * 120)
    print(q, PDF[q].replace(R, ""), "pages", len(doc))
    for pno in range(len(doc)):
        pg = doc[pno]
        rows, free = rows_from_page(pg, pageno=pno + 1)
        labs = [r.label for r in rows]
        if not any("부채총계" in l for l in labs):
            continue
        print(f"-- page {pno + 1}")
        for r in rows:
            if any(k in r.label for k in KEY) and "재보험계약부채" not in r.label or "부채총계" in r.label or "특별계정부채" in r.label:
                print(f"   {r.label[:28]:<30s} vals={[int(v) if float(v).is_integer() else v for v in r.vals]} xs={[round(x) for x in r.xs]}")
