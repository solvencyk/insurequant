# -*- coding: utf-8 -*-
"""Dump full text of the target pages to see EVERY row printed, not just the ones we extract."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

targets = [
    ("data/disclosure/FY2024_Q4/raw/KR0075_비엔피파리바카디프생명보험.pdf", "BNP카디프 2024.4Q", [48, 49, 50]),
    ("data/disclosure/FY2025_Q1/raw/KR0075_비엔피파리바카디프생명보험.pdf", "BNP카디프 2025.1Q", [18, 19, 20]),
    ("data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", "동양생명 2025.2Q", [14, 15, 16]),
]

for path, label, pages in targets:
    doc = fitz.open(path)
    print(f"########## {label} ({path}) ##########")
    for pno in pages:
        if pno >= doc.page_count:
            continue
        page = doc[pno]
        text = page.get_text()
        print(f"----- page index {pno} -----")
        print(text)
        print()
    doc.close()
