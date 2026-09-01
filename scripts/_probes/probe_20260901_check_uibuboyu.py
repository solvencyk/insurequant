# -*- coding: utf-8 -*-
"""Check whether '의무보유부동산' is a generic K-ICS 부동산위험액 template phrase
(appears across other insurers too) or Samsung-specific wording."""
import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
PDF_DIR = REPO / "data" / "disclosure" / "FY2026_Q2" / "pdf"
for code in ("KR0002", "KR0032", "KR0068", "KR0104"):
    matches = list(PDF_DIR.glob(f"{code}_*.pdf"))
    if not matches:
        continue
    doc = fitz.open(matches[0])
    hit_pages = []
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if "의무보유부동산" in t:
            hit_pages.append(i + 1)
    print(f"{code}: '의무보유부동산' found on pages {hit_pages}")
    doc.close()
