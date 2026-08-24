# -*- coding: utf-8 -*-
"""General-purpose K-ICS raw PDF page renderer for vision judgment calls (read-only).

Renders arbitrary pages of any raw disclosure PDF to PNG at a given DPI, for Read-tool
vision inspection. Generalizes the one-off `render_kr0010_2025q1.py` pattern used to
verify KB손해 2025.1Q's SOURCE_UNREADABLE_NOT_VERIFIED pair (inbox 20260821T0620Z) —
reused across 9 more (company,quarter) pairs in the 2026-08-24 follow-up round.

Usage:
    python render_kics_pages.py <pdf_path> <out_prefix> <0idx_pages_csv> [dpi] [out_dir]

Example (KB손해 2025.3Q, pages 13-18 at dpi 240, written to out/):
    python render_kics_pages.py \
        "data/disclosure/FY2025_Q3/raw/KR0010_KB손해보험.pdf" \
        kr0010_2025q3 "13,14,15,16,17,18" 240 out
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

pdf_path = Path(sys.argv[1])
out_prefix = sys.argv[2]
pages = [int(x) for x in sys.argv[3].split(",")]
dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 220
out_dir = Path(sys.argv[5]) if len(sys.argv) > 5 else Path(".")
out_dir.mkdir(parents=True, exist_ok=True)

doc = fitz.open(pdf_path)
for i in pages:
    if i < 0 or i >= doc.page_count:
        print(f"skip {i} (out of range, page_count={doc.page_count})")
        continue
    pix = doc[i].get_pixmap(dpi=dpi)
    out_path = out_dir / f"{out_prefix}_p{i:02d}.png"
    pix.save(str(out_path))
    print(f"saved {out_path} ({pix.width}x{pix.height})")
doc.close()
