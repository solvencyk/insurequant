"""KR0032 raw-PDF reconstruction of the 지급여력금액 자본구성 table (items 4-13).

Reads the raw 정기경영공시 PDF with fitz (PyMuPDF), reconstructs rows by
y-bucketing words and x-sorting inside each bucket (docling MD is not trusted
for row/label alignment). Localizes pages by the parent label
"건전성감독기준 재무상태표" / "이익잉여금".

Output: JSON + human-readable dump to stdout.
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # PyMuPDF

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TARGETS = [
    ("2023.2Q", "data/disclosure/FY2023_Q2/raw/KR0032_NH농협손해보험_amended.pdf"),
    ("2023.3Q", "data/disclosure/FY2023_Q3/raw/KR0032_NH농협손해보험_amended.pdf"),
    ("2024.4Q", "data/disclosure/FY2024_Q4/raw/KR0032_NH농협손해보험.pdf"),
    # controls (quarters where the two masters agree)
    ("2023.1Q", "data/disclosure/FY2023_Q1/raw/KR0032_NH농협손해보험_amended.pdf"),
    ("2024.3Q", "data/disclosure/FY2024_Q3/raw/KR0032_NH농협손해보험_amended.pdf"),
]

ANCHORS = ("이익잉여금", "건전성감독기준", "지급여력금액")


def page_rows(page, ybucket=3.0):
    """words -> y buckets -> x-sorted row strings."""
    words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
    buckets = {}
    for w in words:
        x0, y0, x1, y1, txt = w[0], w[1], w[2], w[3], w[4]
        key = round(y0 / ybucket)
        buckets.setdefault(key, []).append((x0, txt))
    rows = []
    for key in sorted(buckets):
        items = sorted(buckets[key], key=lambda t: t[0])
        rows.append((key * ybucket, [t[1] for t in items]))
    return rows


def main():
    out = {}
    for period, rel in TARGETS:
        path = os.path.join(ROOT, rel)
        print("=" * 100)
        print(f"### {period}  {rel}")
        if not os.path.exists(path):
            print("   MISSING FILE")
            continue
        doc = fitz.open(path)
        print(f"   pages={doc.page_count}")
        hits = []
        for pno in range(doc.page_count):
            txt = doc[pno].get_text("text")
            if "이익잉여금" in txt and ("지급여력금액" in txt or "건전성감독기준" in txt):
                hits.append(pno)
            # text-density check (scan detection)
        print(f"   candidate pages (0-based): {hits}")
        # text density per page, first 20 pages
        dens = [(pno, len(doc[pno].get_text("text"))) for pno in range(min(doc.page_count, 30))]
        print("   text chars/page (first 30):", dens)
        out[period] = {"pages": hits, "rows": {}}
        for pno in hits[:4]:
            print(f"   ---- page {pno + 1} (1-based) ----")
            rows = page_rows(doc[pno])
            captured = []
            for y, cells in rows:
                line = " | ".join(cells)
                captured.append({"y": y, "cells": cells})
                print(f"      y={y:7.1f}  {line}")
            out[period]["rows"][str(pno + 1)] = captured
        doc.close()
    dst = os.path.join(ROOT, "data", "_derived", "_probe_20260920_kr0032_raw_capital.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print()
    print("written:", dst)


if __name__ == "__main__":
    main()
