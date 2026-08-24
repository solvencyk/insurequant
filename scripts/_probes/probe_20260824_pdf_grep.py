"""Read-only: search a raw PDF's text layer for literal substrings (whitespace-insensitive).

Usage: python probe_20260824_pdf_grep.py <pdf> "<needle1>||<needle2>||..."
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

pdf = Path(sys.argv[1])
needles = sys.argv[2].split("||")
doc = fitz.open(pdf)
pages = [doc[i].get_text() for i in range(doc.page_count)]
flat = [t.replace(" ", "").replace("\n", "") for t in pages]
for n in needles:
    f = n.replace(" ", "")
    hits = [i + 1 for i, t in enumerate(flat) if f in t]
    print(f"'{n}' -> {len(hits)} pages {hits[:40]}")
doc.close()
