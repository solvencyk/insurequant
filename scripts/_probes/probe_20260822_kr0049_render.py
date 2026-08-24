# -*- coding: utf-8 -*-
"""Render zero-text-layer pages of KR0049 FY2024_Q3 PDF to PNG for visual inspection."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

import fitz  # noqa: E402

PDF = REPO / "data" / "disclosure" / "FY2024_Q3" / "raw" / "KR0049_악사손해보험.pdf"
OUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "scripts" / "_probes"


def main() -> int:
    doc = fitz.open(PDF)
    pages = [int(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else [4, 6, 16, 17]
    for i in pages:
        page = doc[i]
        pix = page.get_pixmap(dpi=200)
        out = OUT_DIR / f"kr0049_2024q3_p{i:02d}.png"
        pix.save(str(out))
        print(f"saved {out} ({pix.width}x{pix.height})")
    doc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
