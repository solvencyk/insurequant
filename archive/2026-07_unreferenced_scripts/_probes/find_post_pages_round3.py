from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

REPO = Path(__file__).resolve().parent.parent.parent

TARGETS = [
    ("FY2025_Q1", "KR0069", "삼성생명"),
    ("FY2024_Q4", "KR0071", "흥국생명보험"),
    ("FY2024_Q4", "KR0087", "동양생명"),
    ("FY2025_Q1", "KR0087", "동양생명"),
    ("FY2025_Q4", "KR0087", "동양생명"),
    ("FY2024_Q4", "KR0097", "하나생명보험"),
]

BREAKDOWN_HINTS = ["기본요구자본", "생명장기", "일반손해보험위험액", "시장위험액", "분산효과"]

for period, code, name in TARGETS:
    pdf_path = REPO / "data" / "disclosure" / period / "raw" / f"{code}_{name}.pdf"
    if not pdf_path.exists():
        print(f"{period} {code}: PDF NOT FOUND at {pdf_path}")
        continue
    doc = fitz.open(pdf_path)
    print(f"=== {period} {code} {name} ({doc.page_count} pages) ===")
    for i, page in enumerate(doc):
        text = page.get_text()
        if "경과조치" not in text:
            continue
        has_post = ("적용 후" in text) or ("적용후" in text) or ("적용  후" in text)
        hint_hits = [h for h in BREAKDOWN_HINTS if h in text]
        is_apply_table = "적용여부" in text
        no_apply_text = "적용하지 않" in text or "미적용" in text
        if has_post or hint_hits or is_apply_table:
            print(f"  page {i+1}: post_marker={has_post} apply_table={is_apply_table} hints={hint_hits} no_apply_text={no_apply_text}")
    doc.close()
    print()
