"""Verify a candidate cell value against the raw PDF text layer (fitz).

Usage:
    probe_20260901_verify_cell_against_rawpdf.py KR0009 73580 52371 ...

For each value it searches every page for the 백만원 form (value*100 with
thousands separators), the 억원 form, and the bare digits, printing the page
number and the whole source line so the number can be read in its row context.
This is the evidence that goes in a patch script's docstring — a number that
cannot be located in the source PDF does not get written.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
PDF_DIR = REPO / "data" / "disclosure" / "FY2026_Q2" / "pdf"


def _forms(value: str) -> list[str]:
    out = []
    try:
        f = float(value.replace(",", ""))
    except ValueError:
        return [value]
    for candidate in (f, f * 100):
        if abs(candidate - round(candidate)) < 1e-6:
            n = int(round(candidate))
            out.append(f"{n:,}")
            out.append(str(n))
        else:
            out.append(f"{candidate:,.2f}")
    return sorted(set(out), key=len, reverse=True)


def main() -> int:
    import fitz

    code = sys.argv[1]
    values = sys.argv[2:]
    pdf = sorted(PDF_DIR.glob(f"{code}_*.pdf"))[0]
    doc = fitz.open(str(pdf))
    pages = [doc.load_page(i).get_text() or "" for i in range(doc.page_count)]
    doc.close()
    print(f"\n=== {pdf.name} ({len(pages)} pages) ===")
    for value in values:
        print(f"\n-- value {value}")
        found = False
        for form in _forms(value):
            if len(form) < 3:
                continue
            for pno, text in enumerate(pages, start=1):
                for line in text.splitlines():
                    if form in line:
                        print(f"   p{pno:<4} [{form}]  {line.strip()[:130]}")
                        found = True
        if not found:
            print("   NOT FOUND in text layer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
