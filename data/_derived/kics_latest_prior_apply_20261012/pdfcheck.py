"""pdfcheck.py (parser-kics, ticket 20261012T2200Z) -- READ-ONLY helpers to look at the printed numbers of a K-ICS disclosure PDF.

  rows_of_page(pdf, page_no)           -> [(y, [(x0, word), ...])] words clustered into table rows by y (page_no is 1-based)
  find_rows(pdf, pages, tokens)        -> rows whose text contains ANY token (e.g. '17,997'); pages None = scan the whole PDF
  fmt_tokens(v)                        -> printed-number substrings for a master value (comma thousands, sign dropped)

Nothing here writes anything.
"""
import re
import sys

import fitz  # PyMuPDF

ROW_TOL = 3.0


def rows_of_page(pdf, page_no, doc=None):
    own = doc is None
    doc = doc or fitz.open(pdf)
    try:
        page = doc[page_no - 1]
        words = page.get_text("words")
        words.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
        rows, cur, cur_y = [], [], None
        for w in words:
            yc = (w[1] + w[3]) / 2
            if cur_y is None or abs(yc - cur_y) <= ROW_TOL:
                cur.append((round(w[0], 1), w[4]))
                cur_y = yc if cur_y is None else (cur_y + yc) / 2
            else:
                rows.append((round(cur_y, 1), sorted(cur)))
                cur, cur_y = [(round(w[0], 1), w[4])], yc
        if cur:
            rows.append((round(cur_y, 1), sorted(cur)))
        return rows
    finally:
        if own:
            doc.close()


def row_text(row):
    return " ".join(w for _x, w in row[1])


def fmt_tokens(v):
    """printed substrings for a master value: 17997 -> ['17,997']; -2190 -> ['2,190']; 328.0 -> ['328']; 12.34 -> ['12.34']"""
    f = abs(float(v))
    if abs(f - round(f)) < 1e-9:
        n = int(round(f))
        return [f"{n:,}"] if n >= 1000 else [str(n)]
    s = f"{f:,.2f}"
    return [s, s.rstrip("0").rstrip(".")]


def find_rows(pdf, pages, tokens, doc=None):
    own = doc is None
    doc = doc or fitz.open(pdf)
    out = []
    try:
        pgs = pages if pages else list(range(1, len(doc) + 1))
        for p in pgs:
            for row in rows_of_page(pdf, p, doc):
                t = row_text(row)
                if any(re.search(r"(?<![\d,.])" + re.escape(tok) + r"(?![\d,]|\.\d)", t) for tok in tokens):
                    out.append((p, row[0], t))
    finally:
        if own:
            doc.close()
    return out


def utf8_stdout():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
