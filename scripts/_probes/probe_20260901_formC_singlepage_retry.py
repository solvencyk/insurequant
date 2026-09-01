"""FORM_C mitigation test: does a single-page re-convert recover a bad_alloc page?

Converts each requested page on its own (page_range=(p,p)) and reports whether
docling returns SUCCESS and how much text/table content comes out.

Usage: probe_20260901_formC_singlepage_retry.py KR0051 29 30 33 34
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
logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(name)s: %(message)s")

PERIOD = "FY2026_Q2"
PDF_DIR = REPO / "data" / "disclosure" / PERIOD / "pdf"


def main() -> int:
    code = sys.argv[1]
    pages = [int(x) for x in sys.argv[2:]]
    pdf = sorted(PDF_DIR.glob(f"{code}_*.pdf"))[0]

    from solvency.parser.docling_parser import _get_docling_converter

    conv = _get_docling_converter()
    print(f"\n=== single-page retry {pdf.name} ===")
    for p in pages:
        try:
            res = conv.convert(str(pdf), page_range=(p, p))
            md = res.document.export_to_markdown()
            n_tables = len(getattr(res.document, "tables", []) or [])
            print(
                f"  p{p:<4} status={res.status}  md_len={len(md):<7} tables={n_tables}"
                f"  errors={len(getattr(res, 'errors', []) or [])}"
            )
            head = " / ".join(x.strip() for x in md.splitlines()[:4] if x.strip())
            print(f"        head: {head[:160]}")
        except Exception as exc:  # noqa: BLE001
            print(f"  p{p:<4} EXCEPTION {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
