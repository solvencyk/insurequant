import fitz
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

targets = [
    (r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2023_Q3\raw\KR0080_에이아이에이생명보험.pdf", "KR0080"),
    (r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2023_Q2\raw\KR0051_신한이지손해보험.pdf", "KR0051"),
]
for path, tag in targets:
    doc = fitz.open(path)
    for i, page in enumerate(doc):
        text = page.get_text()
        if "순자산" in text and ("경과조치 적용 전" in text or "지급여력비율 세부" in text):
            print(f"===== {tag} page {i+1} =====")
            print(text)
            print()
