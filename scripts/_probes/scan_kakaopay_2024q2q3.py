import fitz
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]

targets = [
    REPO / "data/disclosure/FY2024_Q2/raw/KR1098_카카오페이손해보험_amended2.pdf",
    REPO / "data/disclosure/FY2024_Q3/raw/KR1098_카카오페이손해보험.pdf",
]
for path in targets:
    print(f"===== {path.name} =====")
    doc = fitz.open(path)
    print(f"page_count={len(doc)}")
    total_chars = 0
    hit_pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        total_chars += len(text)
        if any(k in text for k in ("지급여력비율", "순자산", "지급여력금액", "K-ICS")):
            hit_pages.append(i + 1)
    print(f"total_chars={total_chars}  hit_pages(지급여력/순자산/K-ICS)={hit_pages[:30]}")
    # sample first page text length + last page
    print(f"page1 chars={len(doc[0].get_text())}  page{len(doc)} chars={len(doc[-1].get_text())}")
    print()
