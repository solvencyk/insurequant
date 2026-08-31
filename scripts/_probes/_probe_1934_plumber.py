import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import pdfplumber

PDF_DIR = "data/disclosure/FY2026_Q2/pdf/"

PLAN = {
    "KR0051": ("KR0051_신한이지손해보험.pdf", [25, 26, 27]),
    "KR0004": ("KR0004_MG_예별손해보험.pdf", [34, 36, 37, 38]),
    "KR0011": ("KR0011_DB손해보험.pdf", [35, 36]),
    "KR0029": ("KR0029_AIG손해보험.pdf", [32, 33]),
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
