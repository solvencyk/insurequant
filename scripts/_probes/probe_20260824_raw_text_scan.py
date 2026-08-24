"""Read-only raw PDF text scan: per-page density + keyword hits.

Usage:
  python probe_20260824_raw_text_scan.py <pdf> [kw1,kw2,...] [dump_pages_1base_csv]
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

pdf = Path(sys.argv[1])
kws = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else []
dump = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[3] else []

doc = fitz.open(pdf)
texts = []
for i in range(doc.page_count):
    texts.append(doc[i].get_text())
total = sum(len(t) for t in texts)
print(f"{pdf.name}: pages={doc.page_count} chars={total} avg={total / max(1, doc.page_count):.0f}/p")

for kw in kws:
    flat = kw.replace(" ", "")
    hits = [i + 1 for i, t in enumerate(texts) if flat in t.replace(" ", "")]
    print(f"  KW '{kw}': {len(hits)} pages -> {hits[:60]}")

# density profile of top-30 densest pages
prof = sorted(((len(t), i + 1) for i, t in enumerate(texts)), reverse=True)[:15]
print("  densest pages (chars, 1-base):", prof)

for p in dump:
    print("=" * 90)
    print(f"--- page {p} (1-base), chars={len(texts[p - 1])} ---")
    print(texts[p - 1])
doc.close()
