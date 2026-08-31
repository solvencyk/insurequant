import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # PyMuPDF

TARGETS = {
    "KR0001_메리츠화재해상보험": "data/disclosure/FY2026_Q2/pdf/KR0001_메리츠화재해상보험.pdf",
    "KR1011_IBK연금보험": "data/disclosure/FY2026_Q2/pdf/KR1011_IBK연금보험.pdf",
    "KR0087_동양생명": "data/disclosure/FY2026_Q2/pdf/KR0087_동양생명.pdf",
    "KR0094_신한라이프생명보험": "data/disclosure/FY2026_Q2/pdf/KR0094_신한라이프생명보험.pdf",
}

for name, path in TARGETS.items():
    print("#" * 100)
    print(f"### {name}  path={path}")
    p = Path(path)
    if not p.exists():
        print("  !! FILE NOT FOUND")
        continue
    doc = fitz.open(str(p))
    print(f"  pages={doc.page_count}")
    hit_pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if "보완자본" in text and ("한도" in text or "안도" in text):
            hit_pages.append(i)
    print(f"  pages with '보완자본'+'한도/안도': {[h+1 for h in hit_pages]}")
    for h in hit_pages[:4]:
        page = doc[h]
        text = page.get_text()
        print(f"  --- page {h+1} full text ---")
        print(text)
        print("  --- end page ---")
    doc.close()
