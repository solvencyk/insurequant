import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import extract_asset_quality as aq
import fitz

code = sys.argv[1]
period = sys.argv[2] if len(sys.argv) > 2 else "FY2026_Q2"

pdf_path = aq.find_pdf(period, code)
print("path:", pdf_path)
doc = fitz.open(pdf_path)
anchor_page = None
for i in range(len(doc)):
    if "가중부실자산" in doc[i].get_text():
        anchor_page = i
        break
print("anchor_page (0-idx):", anchor_page)

for pno in (anchor_page, anchor_page + 1):
    page = doc[pno]
    print(f"\n=== page {pno+1} sort=True ===")
    txt = page.get_text(sort=True)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    for idx, l in enumerate(lines):
        print(f"{idx:3d}: {l!r}")
doc.close()
