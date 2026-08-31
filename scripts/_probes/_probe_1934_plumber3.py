import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import pdfplumber

PDF_DIR = "data/disclosure/FY2026_Q2/pdf/"

PLAN = {
    "KR0094": ("KR0094_신한라이프생명보험.pdf", [28, 29]),
    "KR0100": ("KR0100_처브라이프생명보험.pdf", [27, 28, 29]),
    "KR0104": ("KR0104_농협생명보험.pdf", [30, 32, 33, 34]),
    "KR1098": ("KR1098_카카오페이손해보험.pdf", [26, 27]),
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
            if not tables:
                print("  (no tables found by plumber) -- raw text below:")
                print(page.extract_text())
            print()

# KR0099 page 34 recheck: dump raw text since table-detect may have missed 자산집중
print("########## KR0099 p34 raw text recheck ##########")
with pdfplumber.open(PDF_DIR + "KR0099_케이비라이프생명보험.pdf") as pdf:
    print(pdf.pages[33].extract_text())
