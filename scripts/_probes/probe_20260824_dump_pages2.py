# -*- coding: utf-8 -*-
"""Dump full text of target pages for 한화생명 2025.2Q and 예별손해 2025.1Q."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

targets = [
    ("data/disclosure/FY2025_Q2/raw/KR0068_한화생명.pdf", "한화생명 2025.2Q", [14, 15, 16, 17, 18]),
    ("data/disclosure/FY2025_Q1/raw/KR0004_예별손해보험.pdf", "예별손해 2025.1Q", [13, 14, 15, 16, 17]),
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
