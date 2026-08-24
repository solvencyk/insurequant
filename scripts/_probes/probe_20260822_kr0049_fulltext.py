# -*- coding: utf-8 -*-
"""Dump full text of specific pages of KR0049 PDF for close reading."""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # noqa: E402

PDF = REPO / "data" / "disclosure" / "FY2024_Q3" / "raw" / "KR0049_악사손해보험.pdf"


def main() -> int:
    doc = fitz.open(PDF)
    pages = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(doc.page_count))
    for i in pages:
        t = doc[i].get_text()
        print(f"===== PAGE idx={i} (disp={i+1}) chars={len(t)} =====")
        print(repr(t))
        print()
    doc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
