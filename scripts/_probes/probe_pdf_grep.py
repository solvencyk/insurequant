"""Print keyword hits with +/- context lines across every page of a disclosure PDF.

usage: probe_pdf_grep.py <period> <KRcode> <keyword> [<after_lines>]
"""
import io, sys
from pathlib import Path
import fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
period, code, kw = sys.argv[1], sys.argv[2], sys.argv[3]
after = int(sys.argv[4]) if len(sys.argv) > 4 else 3
pdf = sorted((ROOT / "data" / "disclosure" / period / "raw").glob(f"{code}_*.pdf"))[0]
doc = fitz.open(pdf)
print(f"# {pdf.name} pages={doc.page_count} kw={kw}")
for i in range(doc.page_count):
    lines = [l.strip() for l in doc[i].get_text().splitlines()]
    for j, l in enumerate(lines):
        if kw in l:
            ctx = [x for x in lines[j:j + after + 1] if x != ""]
            print(f"  p{i+1} L{j}: {' | '.join(ctx)}")
