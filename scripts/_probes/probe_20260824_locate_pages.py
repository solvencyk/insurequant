# -*- coding: utf-8 -*-
"""Locate pages containing '보완자본 한도' keyword across the 5 target filings."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

targets = [
    ("data/disclosure/FY2024_Q4/raw/KR0075_비엔피파리바카디프생명보험.pdf", "BNP카디프 2024.4Q"),
    ("data/disclosure/FY2025_Q1/raw/KR0075_비엔피파리바카디프생명보험.pdf", "BNP카디프 2025.1Q"),
    ("data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", "동양생명 2025.2Q"),
    ("data/disclosure/FY2025_Q2/raw/KR0068_한화생명.pdf", "한화생명 2025.2Q"),
    ("data/disclosure/FY2025_Q1/raw/KR0004_예별손해보험.pdf", "예별손해 2025.1Q"),
]

for path, label in targets:
    doc = fitz.open(path)
    print(f"=== {label} ({path}) — {doc.page_count} pages ===")
    for i, page in enumerate(doc):
        text = page.get_text()
        if "보완자본 한도" in text or "공통적용 경과조치" in text or "해약환급금" in text and "초과분" in text:
            hits = []
            if "보완자본 한도" in text:
                hits.append("보완자본한도")
            if "공통적용 경과조치" in text:
                hits.append("공통적용경과조치")
            print(f"  page {i} (printed ~{i}): {hits}, textlen={len(text)}")
    doc.close()
    print()
