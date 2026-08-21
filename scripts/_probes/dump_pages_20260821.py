"""Dump raw text of specific PDF pages via fitz, for manual column/unit verification.
Usage: python dump_pages_20260821.py <pdf_path> <page1> [page2 ...]
Page numbers are 1-indexed (as printed in the PDF / cited in tickets).
"""
import sys
import io
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main():
    pdf_path = sys.argv[1]
    pages = [int(p) for p in sys.argv[2:]]
    doc = fitz.open(pdf_path)
    print(f"=== {pdf_path} === total pages: {doc.page_count}")
    for p in pages:
        idx = p - 1
        if idx < 0 or idx >= doc.page_count:
            print(f"--- page {p}: OUT OF RANGE ---")
            continue
        text = doc[idx].get_text()
        print(f"\n----------------- page {p} (chars={len(text)}) -----------------")
        print(text)


if __name__ == "__main__":
    main()
