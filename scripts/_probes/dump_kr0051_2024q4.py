import fitz
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
path = REPO / "data/disclosure/FY2024_Q4/raw/KR0051_신한이지손해보험.pdf"
doc = fitz.open(path)
for i, page in enumerate(doc):
    text = page.get_text()
    if "순자산" in text and "건전성감독기준" in text and ("경과조치 적용 전" in text or "지급여력비율 세부" in text):
        print(f"===== page {i+1} =====")
        print(text)
