"""b4_page_density.py PDF [first last] -- characters of text layer per page (READ-ONLY); image-only pages show ~0."""
import sys

import fitz

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from pdfcheck import utf8_stdout  # noqa: E402

utf8_stdout()
pdf = sys.argv[1]
doc = fitz.open(pdf)
a = int(sys.argv[2]) if len(sys.argv) > 2 else 1
b = int(sys.argv[3]) if len(sys.argv) > 3 else len(doc)
print(pdf.split("/")[-1], "pages", len(doc))
out = []
for p in range(a, min(b, len(doc)) + 1):
    page = doc[p - 1]
    t = page.get_text("text")
    imgs = len(page.get_images(full=True))
    out.append(f"p{p}:{len(t)}c/{imgs}img")
print("  ".join(out))
