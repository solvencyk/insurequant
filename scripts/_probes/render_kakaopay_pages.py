import fitz
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

jobs = [
    (REPO / "data/disclosure/FY2024_Q3/raw/KR1098_카카오페이손해보험.pdf", "q3", list(range(1, 20))),
    (REPO / "data/disclosure/FY2024_Q2/raw/KR1098_카카오페이손해보험_amended2.pdf", "q2", list(range(1, 46))),
]
for path, tag, pages in jobs:
    doc = fitz.open(path)
    for p in pages:
        if p > len(doc):
            continue
        page = doc[p - 1]
        pix = page.get_pixmap(dpi=100)
        out_path = OUT / f"{tag}_p{p:02d}.png"
        pix.save(str(out_path))
    print(f"{tag}: rendered {min(len(pages), len(doc))} pages to {OUT}")
