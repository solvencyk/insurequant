"""Locate/dump pages of a disclosure PDF, resolved by (period, KR-code).

usage:
  probe_pdf_pages.py <period> <KRcode> find <keyword> [...]
  probe_pdf_pages.py <period> <KRcode> dump <page_from> [<page_to>]
"""
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
period, code, mode = sys.argv[1], sys.argv[2], sys.argv[3]
cands = sorted((ROOT / "data" / "disclosure" / period / "raw").glob(f"{code}_*.pdf"))
if not cands:
    sys.exit(f"no pdf for {code} in {period}")
pdf = cands[0]
doc = fitz.open(pdf)
print(f"# {pdf.name}  pages={doc.page_count}")
if mode == "find":
    kws = sys.argv[4:]
    for i in range(doc.page_count):
        t = doc[i].get_text()
        hits = [k for k in kws if k in t]
        if hits:
            print(f"p{i+1}: {hits}  chars={len(t)}")
else:
    a = int(sys.argv[4])
    b = int(sys.argv[5]) if len(sys.argv) > 5 else a
    for i in range(a - 1, min(b, doc.page_count)):
        print(f"\n########## PAGE {i+1} ##########")
        print(doc[i].get_text())
