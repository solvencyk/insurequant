"""Find pages in the raw PDF that mention '경과조치 적용 후' near a SCR-breakdown
keyword, for companies whose MD lacks a detected post-transition breakdown table."""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # PyMuPDF

REPO = Path(__file__).resolve().parent.parent.parent

CODES = {
    "KR0073": "교보생명보험",
    "KR0097": "하나생명보험",
    "KR0003": "롯데손해보험",
    "KR0104": "농협생명보험",
}

BREAKDOWN_HINTS = ["기본요구자본", "생명장기", "일반손해보험위험액", "시장위험액", "분산효과"]

for code, name in CODES.items():
    pdf_path = REPO / "data" / "disclosure" / "FY2026_Q1" / "raw" / f"{code}_{name}.pdf"
    if not pdf_path.exists():
        print(f"{code}: PDF NOT FOUND at {pdf_path}")
        continue
    doc = fitz.open(pdf_path)
    print(f"=== {code} {name} ({doc.page_count} pages) ===")
    for i, page in enumerate(doc):
        text = page.get_text()
        if "경과조치" not in text:
            continue
        has_post = ("적용 후" in text) or ("적용후" in text) or ("적용  후" in text)
        hint_hits = [h for h in BREAKDOWN_HINTS if h in text]
        if has_post or hint_hits:
            print(f"  page {i+1}: post_marker={has_post} hints={hint_hits}")
    doc.close()
    print()
