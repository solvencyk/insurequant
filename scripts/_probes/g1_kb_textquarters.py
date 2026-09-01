# -*- coding: utf-8 -*-
import fitz, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

paths = {
    "2023.4Q": "data/disclosure/FY2023_Q4/raw/KR0010_KB손해보험.pdf",
    "2024.2Q": "data/disclosure/FY2024_Q2/raw/KR0010_KB손해보험_amended.pdf",
    "2024.4Q": "data/disclosure/FY2024_Q4/raw/KR0010_KB손해보험.pdf",
    "2025.2Q": "data/disclosure/FY2025_Q2/raw/KR0010_KB손해보험.pdf",
    "2025.4Q": "data/disclosure/FY2025_Q4/raw/KR0010_KB손해보험.pdf",
}
for q, p in paths.items():
    doc = fitz.open(p)
    found = False
    for pno in range(doc.page_count):
        t = doc[pno].get_text()
        if "기타 요구자본" in t:
            found = True
            lines = t.split("\n")
            idx = next(i for i, l in enumerate(lines) if "기타 요구자본" in l)
            lo, hi = max(0, idx - 3), min(len(lines), idx + 30)
            print(f"=== {q} page={pno} ===")
            for j in range(lo, hi):
                print(f"  {j:4d}: {repr(lines[j])}")
    if not found:
        print(f"=== {q}: NOT FOUND via direct text search ===")
    doc.close()
