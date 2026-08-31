"""Dump fitz-extracted text of a page range (or pages containing a keyword) from a raw PDF.
Usage:
  python dump_pdf_pages.py <pdf_path> --pages 10-15
  python dump_pdf_pages.py <pdf_path> --find "키워드" [--context 1]
"""
import argparse
import io
import sys

import fitz  # PyMuPDF

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf_path")
    ap.add_argument("--pages", help="e.g. 10-15 (1-indexed, inclusive)")
    ap.add_argument("--find", help="keyword to locate pages")
    ap.add_argument("--context", type=int, default=0, help="pages of context around find hits")
    args = ap.parse_args()

    doc = fitz.open(args.pdf_path)
    print(f"PDF: {args.pdf_path}  pages={doc.page_count}")

    if args.pages:
        a, b = args.pages.split("-")
        pages = range(int(a) - 1, int(b))
    elif args.find:
        hits = []
        for i in range(doc.page_count):
            t = doc[i].get_text()
            if args.find in t:
                hits.append(i)
        print(f"'{args.find}' found on pages (1-indexed): {[h+1 for h in hits]}")
        pages = set()
        for h in hits:
            for p in range(max(0, h - args.context), min(doc.page_count, h + args.context + 1)):
                pages.add(p)
        pages = sorted(pages)
    else:
        print("need --pages or --find")
        return

    for i in pages:
        print(f"\n===== PAGE {i+1} =====")
        print(doc[i].get_text())


if __name__ == "__main__":
    main()
