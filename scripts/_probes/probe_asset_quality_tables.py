"""Dump raw PDF page text (fitz) and pdfplumber table extraction for specific
company/page targets, to design the section-3 (asset quality / securities)
table parser.

Usage: venv python scripts/_probes/probe_asset_quality_tables.py <period_dir> <code> <page1> [page2 ...]
Pages are 1-indexed (as printed by probe_asset_quality_pages.py).
"""
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import fitz


def find_pdf(period_dir, code_prefix):
    pdf_dir = os.path.join("data", "disclosure", period_dir, "pdf")
    for fn in os.listdir(pdf_dir):
        if fn.startswith(code_prefix + "_") and fn.lower().endswith(".pdf"):
            return os.path.join(pdf_dir, fn)
    return None


def main():
    args = sys.argv[1:]
    period_dir = args[0]
    code = args[1]
    pages = [int(x) for x in args[2:]]
    path = find_pdf(period_dir, code)
    print(f"path={path}")

    doc = fitz.open(path)
    for p in pages:
        print(f"\n===== fitz text page {p} =====")
        text = doc[p - 1].get_text()
        print(text)
    doc.close()

    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            for p in pages:
                print(f"\n===== pdfplumber tables page {p} =====")
                page = pdf.pages[p - 1]
                tables = page.extract_tables()
                for ti, t in enumerate(tables):
                    print(f"--- table {ti} ({len(t)} rows) ---")
                    for row in t:
                        print(row)
    except Exception as e:
        print(f"pdfplumber error: {e}")


if __name__ == "__main__":
    main()
