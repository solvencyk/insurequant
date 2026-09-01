# -*- coding: utf-8 -*-
"""Scan all 11 KB (KR0010) target quarters for the '비례성원칙 적용에 관한 사항'
subsidiary table (item25 source) and check for any '관계회사'+'요구자본' analog
(possible item26 source). Also report whether item24-style '업권별 자본규제'
wording appears anywhere (would indicate a genuine, separate item24 source)."""
from __future__ import annotations
import fitz, io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]

TARGETS = [
    ("2023.4Q", "data/disclosure/FY2023_Q4/raw/KR0010_KB손해보험.pdf"),
    ("2024.1Q", "data/disclosure/FY2024_Q1/raw/KR0010_KB손해보험_amended.pdf"),
    ("2024.3Q", "data/disclosure/FY2024_Q3/raw/KR0010_KB손해보험_amended.pdf"),
    ("2024.4Q", "data/disclosure/FY2024_Q4/raw/KR0010_KB손해보험.pdf"),
    ("2025.1Q", "data/disclosure/FY2025_Q1/raw/KR0010_KB손해보험.pdf"),
    ("2025.2Q", "data/disclosure/FY2025_Q2/raw/KR0010_KB손해보험.pdf"),
    ("2025.3Q", "data/disclosure/FY2025_Q3/raw/KR0010_KB손해보험.pdf"),
    ("2025.4Q", "data/disclosure/FY2025_Q4/raw/KR0010_KB손해보험.pdf"),
    ("2026.1Q", "data/disclosure/FY2026_Q1/raw/KR0010_KB손해보험.pdf"),
]

for tq, relpath in TARGETS:
    p = REPO / relpath
    if not p.exists():
        print(f"=== {tq}: FILE MISSING {relpath} ===")
        continue
    doc = fitz.open(p)
    print(f"=== {tq}: pages={doc.page_count} ===")
    hit_pages = []
    for pno in range(doc.page_count):
        t = doc[pno].get_text()
        if "비례성원칙" in t and ("간편법" in t or "요구자본" in t):
            hit_pages.append(pno)
    print(f"  비례성원칙 hit pages: {hit_pages}")
    for pno in hit_pages:
        t = doc[pno].get_text()
        if "총자산" in t and ("LIG" in t or "PT." in t or "8%" in t or "8 %" in t):
            print(f"  --- page {pno} (subsidiary table candidate) ---")
            print("  " + t.replace("\n", " | "))
    # item26 관계회사 analog check
    for pno in range(doc.page_count):
        t = doc[pno].get_text()
        if "관계회사" in t and "요구자본" in t:
            print(f"  관계회사+요구자본 co-occur on page {pno}")
    doc.close()
    print()
