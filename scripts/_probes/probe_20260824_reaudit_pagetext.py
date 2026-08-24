# -*- coding: utf-8 -*-
"""Read-only: dump raw PDF page text (fitz) with per-page char density, to a UTF-8 file.

usage: probe_20260824_reaudit_pagetext.py <pdf> <pages 1-base csv or 'find:<kw>'> <outname>
"""
import sys
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "artifacts" / "validation"

pdf = Path(sys.argv[1])
if not pdf.is_absolute():
    pdf = ROOT / pdf
spec = sys.argv[2]
out = OUTDIR / sys.argv[3]

doc = fitz.open(pdf)
buf = [f"FILE {pdf}  pages={doc.page_count}"]

if spec.startswith("find:"):
    kws = spec[5:].split("|")
    hits = []
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if any(k in t.replace(" ", "") for k in [k.replace(" ", "") for k in kws]):
            hits.append(i + 1)
    buf.append(f"KEYWORD {kws} -> pages {hits}")
    pages = hits
else:
    pages = [int(x) for x in spec.split(",") if x.strip()]

for p in pages:
    page = doc[p - 1]
    t = page.get_text()
    buf.append("=" * 90)
    buf.append(f"--- page {p}  chars={len(t)} ---")
    buf.append(t)
OUTDIR.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(buf), encoding="utf-8")
print("wrote", out, "pages", pages)
