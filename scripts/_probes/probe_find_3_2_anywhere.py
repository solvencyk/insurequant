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
anchor1 = None
best_page, best_score = None, 0
for i in range(len(doc)):
    txt = doc[i].get_text()
    if anchor1 is None and "가중부실자산" in txt:
        anchor1 = i
    toks = [aq._compact(t) for t in txt.split()]
    score = sum(1 for t in toks if t in aq.LEAF_KEYWORDS or t in aq._LEAF_ALIASES)
    if score > best_score:
        best_score, best_page = score, i
print(f"anchor1 (가중부실자산) page(0idx)={anchor1}")
print(f"best leaf-density page(0idx)={best_page} score={best_score}")
print("n_pages:", len(doc))
doc.close()
