# -*- coding: utf-8 -*-
"""KB손해(KR0010) 2025.1Q raw 를 고해상도로 렌더링해 scratchpad 에 저장 (vision 판독용)."""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
PAGES = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else list(range(26))
DPI = int(sys.argv[3]) if len(sys.argv) > 3 else 260

raw = REPO / "data" / "disclosure" / "FY2025_Q1" / "raw"
pdf = max(sorted(raw.glob("KR0010_*.pdf")), key=lambda p: p.stat().st_size)
doc = fitz.open(pdf)
for i in PAGES:
    if i < 0 or i >= doc.page_count:
        continue
    pix = doc[i].get_pixmap(dpi=DPI)
    out_path = OUT / f"kr0010_2025q1_p{i:02d}.png"
    pix.save(str(out_path))
    print(f"saved {out_path} ({pix.width}x{pix.height})")
doc.close()
