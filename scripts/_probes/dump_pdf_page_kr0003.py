import fitz
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

path = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2023_Q4\raw\KR0003_롯데손해보험_amended.pdf"
doc = fitz.open(path)
for i, page in enumerate(doc):
    text = page.get_text()
    if "순자산" in text and ("경과조치 적용 전" in text or "지급여력비율 세부" in text):
        print(f"===== page {i+1} =====")
        print(text)
        print()
