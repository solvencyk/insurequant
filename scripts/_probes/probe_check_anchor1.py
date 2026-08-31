import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import extract_asset_quality as aq
import fitz

code = sys.argv[1]
period = sys.argv[2]

pdf_path = aq.find_pdf(period, code)
print("path:", pdf_path)
doc = fitz.open(pdf_path)
print("pages:", len(doc))
found_pages = []
for i in range(len(doc)):
    txt = doc[i].get_text()
    if "가중부실" in txt or "부실자산" in txt or "자산건전성" in txt:
        found_pages.append(i)
print("pages mentioning 가중부실/부실자산/자산건전성:", found_pages[:20])
if found_pages:
    p = found_pages[0]
    print(f"\n--- page {p+1} sort=True (first hit) ---")
    print(doc[p].get_text(sort=True)[:2500])
doc.close()
