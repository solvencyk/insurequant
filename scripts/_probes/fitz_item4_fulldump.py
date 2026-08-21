import fitz
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "disclosure"

TARGETS = [
    ("FY2023_Q1/raw/KR0051_신한이지손해보험.pdf", 8),
    ("FY2023_Q1/raw/KR0071_흥국생명보험_amended.pdf", 8),
    ("FY2023_Q2/raw/KR0074_라이나생명보험_amended.pdf", 11),
    ("FY2023_Q3/raw/KR0051_신한이지손해보험.pdf", 9),
    ("FY2023_Q4/raw/KR0051_신한이지손해보험.pdf", 25),
    ("FY2024_Q4/raw/KR0051_신한이지손해보험.pdf", 31),
    ("FY2023_Q2/raw/KR0080_에이아이에이생명보험.pdf", 8),
    ("FY2023_Q4/raw/KR1098_카카오페이손해보험.pdf", 21),
]

for rel, pageno in TARGETS:
    path = RAW / rel
    doc = fitz.open(path)
    page = doc[pageno - 1]
    print(f"===== {rel} page {pageno} =====")
    print(page.get_text())
    print()
