"""Read-only: dump the reconstructed rows (label + numbers) of one disclosure PDF page.

usage: python s31_pdf_page_rows.py <FYyyyy_Qn> <KR code> <page(1-based)> [--max 60]
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import fitz  # noqa: E402

import extract_lina_csm_rows_20261011 as L  # noqa: E402
from _disclosure_pdf_paths import latest_disclosure_pdfs  # noqa: E402

fitz.TOOLS.mupdf_display_errors(False)
fy, kr, pno = sys.argv[1], sys.argv[2], int(sys.argv[3])
mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 60
pdf = latest_disclosure_pdfs(fy, kr)[0]
doc = fitz.open(pdf)
page = doc[pno - 1]
print(pdf.name, "page", pno, "of", len(doc))
txt = page.get_text()
print("TEXT HEAD:", [ln.strip() for ln in txt.splitlines() if ln.strip()][:6])
for r in L.page_rows(page)[:mx]:
    lab, nums = L.split_row(r)
    print(f"  {lab[:50]:50s} {nums}")
