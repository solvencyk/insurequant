# -*- coding: utf-8 -*-
"""investigation probe (read-only) - KR0049 (AXA sonhae) TFI section page-by-page scan.

Purpose: confirm whether [ci-icig biyul ui gyeongwajochi jeogyong e gwanhan sahang]
1) gongtongjeogyong gyeongwajochi table (items 47/48/49/50/51) exists in the raw PDF,
   and if so on which page, and whether that page has a text layer or is scanned.

No writes. Just diagnostics.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # noqa: E402

PDF = REPO / "data" / "disclosure" / "FY2024_Q3" / "raw" / "KR0049_악사손해보험.pdf"

KEYWORDS = ["경과조치", "공통적용", "보완자본", "한도", "해약환급금", "지급여력기준금액",
            "기본자본", "지급여력금액", "선택적용"]


def main() -> int:
    doc = fitz.open(PDF)
    n = doc.page_count
    print(f"PDF={PDF.name}  pages={n}  size={PDF.stat().st_size:,} bytes")
    print("=" * 100)

    page_texts = [doc[i].get_text() for i in range(n)]
    total_chars = sum(len(t) for t in page_texts)
    print(f"total_chars={total_chars}  avg_density={total_chars / n:.1f} chars/page")
    print("=" * 100)

    for i, t in enumerate(page_texts):
        nchars = len(t)
        hits = [kw for kw in KEYWORDS if kw in t]
        first_line = t.strip().splitlines()[0] if t.strip() else "(EMPTY)"
        print(f"[p{i:02d} disp={i+1:02d}] chars={nchars:5d}  hits={hits}")
        print(f"         first_line={first_line[:80]!r}")

    print("=" * 100)
    print("PAGES WITH ANY KEYWORD HIT:")
    for i, t in enumerate(page_texts):
        hits = [kw for kw in KEYWORDS if kw in t]
        if hits:
            print(f"  p{i:02d} (disp {i+1:02d}): {hits}")

    doc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
