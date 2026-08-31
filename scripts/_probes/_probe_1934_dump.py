import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

PDF_DIR = "data/disclosure/FY2026_Q2/pdf/"

# code -> (pdf filename, [1-indexed pages to dump])
PLAN = {
    "KR0004": ("KR0004_MG_예별손해보험.pdf", [34, 35, 36, 37, 38]),
    "KR0011": ("KR0011_DB손해보험.pdf", [35, 36]),
    "KR0029": ("KR0029_AIG손해보험.pdf", [32, 33]),
    "KR0051": ("KR0051_신한이지손해보험.pdf", [19, 25, 26, 27, 28]),
}

for code, (fname, pages) in PLAN.items():
    doc = fitz.open(PDF_DIR + fname)
    print(f"########## {code} ({fname}, {doc.page_count}p) ##########")
    for p in pages:
        idx = p - 1
        if idx < 0 or idx >= doc.page_count:
            continue
        print(f"----- page {p} -----")
        print(doc[idx].get_text())
        print()
    doc.close()
