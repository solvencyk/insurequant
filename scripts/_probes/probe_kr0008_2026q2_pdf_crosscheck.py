import io
import sys
sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # PyMuPDF

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0008_삼성화재해상보험.pdf"

doc = fitz.open(PDF)
print("pages:", doc.page_count)

targets = ["금리위험액 현황", "주식위험액 현황", "부동산위험액 현황", "외환위험액 현황", "자산집중위험액 현황"]
hit_pages = {}
for i in range(doc.page_count):
    text = doc[i].get_text()
    for t in targets:
        if t in text and t not in hit_pages:
            hit_pages[t] = i

print(hit_pages)

for t, i in sorted(hit_pages.items(), key=lambda kv: kv[1]):
    print(f"\n===== {t} (page index {i}, page num {i+1}) =====")
    print(doc[i].get_text())
    if i + 1 < doc.page_count:
        print(f"--- next page {i+2} ---")
        print(doc[i + 1].get_text())
