import fitz
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
path = REPO / "data/disclosure/FY2023_Q2/raw/KR0087_동양생명.pdf"
doc = fitz.open(path)
print(f"page_count={len(doc)}")
for i, page in enumerate(doc):
    text = page.get_text()
    if any(k in text for k in ("경과조치", "신청현황", "시장위험", "금리위험", "주식위험")):
        print(f"===== page {i+1} =====")
        print(text)
        print()
