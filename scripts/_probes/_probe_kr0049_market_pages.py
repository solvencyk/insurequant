import fitz
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = "data/disclosure/FY2026_Q2/pdf/KR0049_악사손해보험.pdf"
doc = fitz.open(PDF)
print(f"Total pages: {len(doc)}")

keywords = [
    "금리위험액", "주식위험액", "부동산위험액", "외환위험액", "자산집중위험액",
    "시장위험 관리", "6-4", "순자산가치", "충격", "평균회귀", "금리평탄", "금리경사",
]

for kw in keywords:
    hits = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if kw in text:
            hits.append(i + 1)  # 1-indexed page number
    print(f"{kw!r}: pages {hits}")
