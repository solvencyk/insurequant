import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
import fitz

print("===== KR0049 악사손해 page3 (1-1) =====")
doc = fitz.open(str(REPO / "data/disclosure/FY2026_Q2/pdf/KR0049_악사손해보험.pdf"))
print(repr(doc[2].get_text()[:600]))
doc.close()

print("\n===== KR0068 한화생명 page3 (1-1) full =====")
doc = fitz.open(str(REPO / "data/disclosure/FY2026_Q2/pdf/KR0068_한화생명.pdf"))
lines = [l for l in doc[2].get_text().splitlines()]
for i, l in enumerate(lines):
    print(i, repr(l))
doc.close()

print("\n===== KR0079 미래에셋생명 pages 1-6 char counts =====")
doc = fitz.open(str(REPO / "data/disclosure/FY2026_Q2/pdf/KR0079_미래에셋생명.pdf"))
for pno in range(min(8, len(doc))):
    t = doc[pno].get_text()
    print(f"page {pno+1}: chars={len(t)}  sample={t[:80]!r}")
doc.close()
