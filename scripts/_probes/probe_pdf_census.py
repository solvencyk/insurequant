"""Per-page text-length census of a disclosure PDF (detect image-only pages)."""
import io, sys
from pathlib import Path
import fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
period, code = sys.argv[1], sys.argv[2]
pdf = sorted((ROOT / "data" / "disclosure" / period / "raw").glob(f"{code}_*.pdf"))[0]
doc = fitz.open(pdf)
print(f"# {pdf.name} pages={doc.page_count} size={pdf.stat().st_size:,}")
for i in range(doc.page_count):
    p = doc[i]
    t = p.get_text().strip()
    imgs = len(p.get_images(full=True))
    first = t.replace("\n", " ")[:70]
    print(f"  p{i+1:>3}: chars={len(t):>6} imgs={imgs:>3} | {first}")
