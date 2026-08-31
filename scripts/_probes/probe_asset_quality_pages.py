"""Probe raw PDFs directly (fitz) for section 3 (자산건전성/유가증권투자) keywords,
bypassing docling MD, to distinguish: (a) genuinely absent, (b) docling window
dropped it (text present in PDF, absent in MD), (c) scanned/no text layer.

Usage: venv python scripts/_probes/probe_asset_quality_pages.py <period_dir> KR0011 KR0087 ...
"""
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import fitz  # PyMuPDF

KEYWORDS = ["자산건전성", "부실자산", "유가증권투자", "유가증권 투자", "평가손익", "고정이하", "요주의", "회수의문", "추정손실"]

def find_pdf(period_dir, code_prefix):
    pdf_dir = os.path.join("data", "disclosure", period_dir, "pdf")
    if not os.path.isdir(pdf_dir):
        return None
    for fn in os.listdir(pdf_dir):
        if fn.startswith(code_prefix + "_") and fn.lower().endswith(".pdf"):
            return os.path.join(pdf_dir, fn)
    return None


def probe(path):
    doc = fitz.open(path)
    n = len(doc)
    print(f"  pages={n}")
    total_chars = 0
    hits = {}
    page_density = []
    for i in range(n):
        page = doc[i]
        text = page.get_text()
        total_chars += len(text)
        page_density.append((i + 1, len(text)))
        for kw in KEYWORDS:
            if kw in text:
                hits.setdefault(kw, []).append(i + 1)
    doc.close()
    avg_density = total_chars / max(n, 1)
    print(f"  total_chars={total_chars}  avg_chars/page={avg_density:.0f}")
    # flag low-density pages (possible scan)
    low = [p for p, c in page_density if c < 50]
    if len(low) > n * 0.5:
        print(f"  ** LOW TEXT DENSITY on {len(low)}/{n} pages -> likely SCANNED **")
    if hits:
        for kw, pages in hits.items():
            print(f"  KEYWORD '{kw}' on pages: {pages}")
    else:
        print("  NO keyword hits anywhere in PDF text layer.")
    return hits, avg_density, n


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print("usage: probe_asset_quality_pages.py <period_dir> <code1> [code2 ...]")
        sys.exit(1)
    period_dir = args[0]
    codes = args[1:]
    for code in codes:
        print(f"===== {code} ({period_dir}) =====")
        path = find_pdf(period_dir, code)
        if not path:
            print("  PDF NOT FOUND")
            continue
        print(f"  path={path}")
        try:
            probe(path)
        except Exception as e:
            print(f"  ERROR: {e}")
        print()


if __name__ == "__main__":
    main()
