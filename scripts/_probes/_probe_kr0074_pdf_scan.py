# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

PDF = r"data/disclosure/FY2026_Q2/pdf/KR0074_라이나생명보험.pdf"
doc = fitz.open(PDF)
print(f"total pages: {doc.page_count}")

keywords = [
    "금리위험액", "주식위험액", "부동산위험액", "외환위험액", "자산집중위험액",
    "충격전", "평균회귀", "금리상승", "금리하락", "금리평탄", "금리경사",
    "순자산가치", "6-4", "시장위험  관리", "시장위험 관리",
]

hits = {}
for i in range(doc.page_count):
    page = doc[i]
    text = page.get_text()
    for kw in keywords:
        if kw in text:
            hits.setdefault(kw, []).append(i + 1)  # 1-indexed

for kw, pages in hits.items():
    print(f"{kw!r}: pages {pages}")

print()
print("=== text density per page (chars), pages 1-197 ===")
densities = []
for i in range(doc.page_count):
    text = page = doc[i].get_text()
    densities.append((i + 1, len(text)))

# print pages with very low density (candidate scans)
low = [d for d in densities if d[1] < 200]
print(f"pages with <200 chars: {len(low)}")
for pg, n in low:
    print(f"  page {pg}: {n} chars")
