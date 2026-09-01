# -*- coding: utf-8 -*-
"""Group1 (현대해상/KB손해/신한이지) item23-26 raw-PDF block dumper.
Prints the text lines around the '기타 요구자본' table for each (company, quarter, pdf)
so we can eyeball exactly what the source prints for items 24/25/26.
"""
from __future__ import annotations
import fitz, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGETS = [
    ("KR0009", "2023.1Q", "data/disclosure/FY2023_Q1/raw/KR0009_현대해상.pdf"),
    ("KR0009", "2023.2Q", "data/disclosure/FY2023_Q2/raw/KR0009_현대해상.pdf"),
    ("KR0009", "2023.3Q", "data/disclosure/FY2023_Q3/raw/KR0009_현대해상_amended.pdf"),
    ("KR0009", "2023.4Q", "data/disclosure/FY2023_Q4/raw/KR0009_현대해상_amended.pdf"),
    ("KR0009", "2024.1Q", "data/disclosure/FY2024_Q1/raw/KR0009_현대해상_amended.pdf"),
    ("KR0009", "2024.2Q", "data/disclosure/FY2024_Q2/raw/KR0009_현대해상_amended.pdf"),
    ("KR0009", "2024.3Q", "data/disclosure/FY2024_Q3/raw/KR0009_현대해상_amended.pdf"),
    ("KR0009", "2024.4Q", "data/disclosure/FY2024_Q4/raw/KR0009_현대해상.pdf"),
    ("KR0009", "2025.1Q", "data/disclosure/FY2025_Q1/raw/KR0009_현대해상.pdf"),
    ("KR0009", "2025.2Q", "data/disclosure/FY2025_Q2/raw/KR0009_현대해상_amended.pdf"),
    ("KR0009", "2025.3Q", "data/disclosure/FY2025_Q3/raw/KR0009_현대해상.pdf"),
    ("KR0009", "2025.4Q", "data/disclosure/FY2025_Q4/raw/KR0009_현대해상.pdf"),
    ("KR0051", "2023.1Q", "data/disclosure/FY2023_Q1/raw/KR0051_신한이지손해보험.pdf"),
    ("KR0051", "2023.2Q", "data/disclosure/FY2023_Q2/raw/KR0051_신한이지손해보험.pdf"),
    ("KR0051", "2023.3Q", "data/disclosure/FY2023_Q3/raw/KR0051_신한이지손해보험.pdf"),
    ("KR0051", "2023.4Q", "data/disclosure/FY2023_Q4/raw/KR0051_신한이지손해보험.pdf"),
    ("KR0051", "2024.1Q", "data/disclosure/FY2024_Q1/raw/KR0051_신한이지손해보험.pdf"),
    ("KR0051", "2024.2Q", "data/disclosure/FY2024_Q2/raw/KR0051_신한이지손해보험.pdf"),
    ("KR0051", "2024.3Q", "data/disclosure/FY2024_Q3/raw/KR0051_신한이지손해보험.pdf"),
    ("KR0051", "2024.4Q", "data/disclosure/FY2024_Q4/raw/KR0051_신한이지손해보험.pdf"),
    ("KR0051", "2026.1Q", "data/disclosure/FY2026_Q1/raw/KR0051_신한이지손해보험.pdf"),
]

for code, q, path in TARGETS:
    try:
        doc = fitz.open(path)
    except Exception as e:
        print(f"### {code} {q}: OPEN FAIL {e}")
        continue
    found = False
    for pno in range(doc.page_count):
        t = doc[pno].get_text()
        if "기타 요구자본" in t or "비례성원칙" in t:
            found = True
            lines = t.split("\n")
            idx = next((i for i, l in enumerate(lines) if "기타 요구자본" in l), None)
            if idx is None:
                idx = next(i for i, l in enumerate(lines) if "비례성원칙" in l)
            lo, hi = max(0, idx - 3), min(len(lines), idx + 25)
            print(f"### {code} {q} page={pno} ###")
            for j in range(lo, hi):
                print(f"  {j:4d}: {repr(lines[j])}")
            break
    if not found:
        print(f"### {code} {q}: '기타 요구자본'/'비례성원칙' NOT FOUND in any page text ###")
    doc.close()
