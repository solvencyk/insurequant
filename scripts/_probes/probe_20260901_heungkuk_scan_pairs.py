# -*- coding: utf-8 -*-
"""Re-run the exact scan_pairs()/resolve() logic from
scripts/fill_post_transition_adjust_items.py against Heungkuk (KR0071) raw PDFs
directly via fitz, bypassing docling MD entirely, to see the TRUE printed
(적용전, 적용후) pairs for item23 (기타요구자본) the fill script itself would have
read -- docling's MD table conversion is a secondary render and may have
misaligned columns relative to what fitz's raw page text actually shows.

Read-only diagnostic. Prints raw candidate pairs per page + the resolved value
(if any) for item22/23, for every KR0071 quarter in the audit list.
"""
import io
import json
import re
import sys
from pathlib import Path

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
DISCLOSURE = REPO / "data" / "disclosure"

ROW_LABELS = {22: "법인세조정액", 23: "기타요구자본"}
PAGE_MUST_HAVE = ("경과조치",)
PAGE_ANY_OF = ("장수위험", "주식위험", "금리위험")


def quarter_to_period(q: str) -> str:
    year, qq = q.split(".")
    return f"FY{year}_Q{qq[0]}"


def find_pdf(code: str, quarter: str):
    raw = DISCLOSURE / quarter_to_period(quarter) / "raw"
    hits = sorted(raw.glob(f"{code}_*.pdf"))
    if not hits:
        return None
    amended = [p for p in hits if "_amended" in p.name]
    return max(amended or hits, key=lambda p: p.stat().st_size)


def scan_pairs(pdf: Path):
    out = {22: [], 23: []}
    doc = fitz.open(pdf)
    try:
        for pno, page in enumerate(doc, start=1):
            text = page.get_text()
            if not all(k in text for k in PAGE_MUST_HAVE):
                continue
            if not any(k in text for k in PAGE_ANY_OF):
                continue
            lines = [l.strip() for l in text.splitlines()]
            for i, line in enumerate(lines):
                for item, label in ROW_LABELS.items():
                    if line != label:
                        continue
                    nxt = [x for x in lines[i + 1:i + 6] if x != ""][:2]
                    if len(nxt) == 2:
                        out[item].append((pno, nxt[0], nxt[1]))
    finally:
        doc.close()
    return out


QUARTERS = [
    "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q",
    "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q",
]

for q in QUARTERS:
    pdf = find_pdf("KR0071", q)
    print(f"\n=== KR0071 {q}  pdf={pdf.name if pdf else None} ===")
    if pdf is None:
        print("  NO RAW PDF")
        continue
    pairs = scan_pairs(pdf)
    for item in (22, 23):
        for pno, pre_tok, post_tok in pairs[item]:
            print(f"  item{item} p{pno}: 전={pre_tok!r} 후={post_tok!r}")
        if not pairs[item]:
            print(f"  item{item}: NO ROW FOUND on any 경과조치 page")
