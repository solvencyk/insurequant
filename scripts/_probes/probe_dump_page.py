import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import extract_asset_quality as aq
import fitz

code = sys.argv[1]
period = sys.argv[2]
page0 = int(sys.argv[3])  # 0-indexed

pdf_path = aq.find_pdf(period, code)
doc = fitz.open(pdf_path)
for p in range(page0, min(page0 + 2, len(doc))):
    print(f"===== page {p+1} (0idx={p}) sort=True =====")
    print(doc[p].get_text(sort=True))
doc.close()
