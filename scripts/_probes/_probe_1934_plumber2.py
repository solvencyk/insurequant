import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import pdfplumber

PDF_DIR = "data/disclosure/FY2026_Q2/pdf/"

PLAN = {
    "KR0068": ("KR0068_한화생명.pdf", [36, 37, 38]),
    "KR0080": ("KR0080_에이아이에이생명보험.pdf", [29, 30, 31]),
    "KR0094": ("KR0094_신한라이프생명보험.pdf", [30, 31, 32]),
    "KR0099": ("KR0099_케이비라이프생명보험.pdf", [32, 33, 34]),
}

for code, (fname, pages) in PLAN.items():
    print(f"########## {code} ##########")
    with pdfplumber.open(PDF_DIR + fname) as pdf:
        for p in pages:
            idx = p - 1
            if idx < 0 or idx >= len(pdf.pages):
                continue
            print(f"----- page {p} -----")
            page = pdf.pages[idx]
            tables = page.extract_tables()
            for ti, tbl in enumerate(tables):
                print(f"  [table {ti}]")
                for row in tbl:
                    print("   ", row)
            print()
