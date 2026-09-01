"""FORM_C decisive experiment: does docling REPORT the dropped pages?

_convert_one() never inspects ``conversion.status`` / ``conversion.errors``.
Docling's pipeline processes pages in batches; when a batch raises (OOM,
model failure) docling logs it, marks the document PARTIAL_SUCCESS and returns
the document WITHOUT those pages. That would produce exactly the observed
"contiguous block of pages missing from a range that was fully selected".

This probe converts one company's real range and prints:
  * conversion.status  (SUCCESS / PARTIAL_SUCCESS / FAILURE)
  * conversion.errors
  * which page numbers actually made it into document.pages
  * per-page character counts in the exported markdown-ish text

Usage:  probe_20260901_formC_docling_status.py KR0051 5 35
"""

from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

PERIOD = "FY2026_Q2"
PDF_DIR = REPO / "data" / "disclosure" / PERIOD / "pdf"


def main() -> int:
    code = sys.argv[1] if len(sys.argv) > 1 else "KR0051"
    lo = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    hi = int(sys.argv[3]) if len(sys.argv) > 3 else 35

    pdfs = sorted(PDF_DIR.glob(f"{code}_*.pdf"))
    if not pdfs:
        print(f"no pdf for {code}")
        return 1
    pdf = pdfs[0]

    from solvency.parser.docling_parser import _get_docling_converter

    conv = _get_docling_converter()
    print(f"\n=== docling convert {pdf.name} page_range=({lo},{hi}) ===")
    result = conv.convert(str(pdf), page_range=(lo, hi))

    status = getattr(result, "status", None)
    print(f"status  = {status}")
    errs = getattr(result, "errors", None)
    print(f"errors  = {errs}")

    doc = result.document
    pages = getattr(doc, "pages", None)
    if pages is not None:
        try:
            keys = sorted(pages.keys())
        except AttributeError:
            keys = list(range(len(pages)))
        print(f"document.pages keys ({len(keys)}): {keys}")
        expected = list(range(lo, hi + 1))
        missing = [p for p in expected if p not in keys]
        print(f"MISSING from document.pages: {missing}")

    # per-page provenance of exported text items
    per_page: dict[int, int] = {}
    for t in getattr(doc, "texts", []) or []:
        for prov in getattr(t, "prov", []) or []:
            pno = getattr(prov, "page_no", None)
            if pno is not None:
                per_page[pno] = per_page.get(pno, 0) + len(getattr(t, "text", "") or "")
    for tb in getattr(doc, "tables", []) or []:
        for prov in getattr(tb, "prov", []) or []:
            pno = getattr(prov, "page_no", None)
            if pno is not None:
                per_page[pno] = per_page.get(pno, 0) + 1000  # marker weight
    print("\npage -> exported char/table weight:")
    for p in range(lo, hi + 1):
        print(f"  p{p:<4} {per_page.get(p, 0)}")
    md = doc.export_to_markdown()
    print(f"\nexport_to_markdown len = {len(md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
