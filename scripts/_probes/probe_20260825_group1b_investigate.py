# -*- coding: utf-8 -*-
"""Group-1B (3 buckets): text is clearly present but the 3-keyword co-occurrence
filter (a AND b AND c on one page) fails. Dump nearby text to see why."""
from __future__ import annotations
import sys, os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout = os.fdopen(1, "w", encoding="utf-8", closefd=False)

import fitz  # noqa: E402
fitz.TOOLS.mupdf_display_errors(False)
fitz.TOOLS.mupdf_display_warnings(False)
import fix_20260821_tier2_limit_lines as T2  # noqa: E402


def dump_pages(code, q, page_idxs):
    pdf = T2._pdf(T2.q2p(q), code)
    print(f"\n########## {code} {q}  pdf={pdf.name if pdf else None}")
    doc = fitz.open(pdf)
    for pi in page_idxs:
        t = doc[pi].get_text()
        print(f"  --- page(0idx={pi}, 1idx={pi+1}) char_len={len(t)}")
        print(t)
        print("  --- end page ---")
    doc.close()


print("=== KR0080 2024.4Q pages 171, 330 (and neighbors) ===")
dump_pages("KR0080", "2024.4Q", [170, 171, 172, 329, 330, 331])

print("\n=== KR0080 2025.4Q pages 174, 341 (and neighbors) ===")
dump_pages("KR0080", "2025.4Q", [173, 174, 175, 340, 341, 342])

print("\n=== KR0071 2024.4Q pages with '한도' -- check for '경과조치'/'지급여력' nearby ===")
pdf = T2._pdf(T2.q2p("2024.4Q"), "KR0071")
doc = fitz.open(pdf)
texts = [doc[i].get_text() for i in range(doc.page_count)]
hits = [i for i, t in enumerate(texts) if "한도" in t]
print(f"전체 '한도' 히트 페이지: {hits}")
for pi in hits:
    t = texts[pi]
    flags = []
    if "경과조치" in t: flags.append("경과조치")
    if "지급여력" in t: flags.append("지급여력")
    if "공통" in t: flags.append("공통")
    if "보완자본" in t: flags.append("보완자본")
    print(f"  page(0idx={pi}) len={len(t)} flags={flags}")
doc.close()
