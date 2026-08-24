# -*- coding: utf-8 -*-
"""Group-1 triage (18 buckets, NO_MATCHED_PAGE): relaxed keyword search to tell
apart 'true scan / font-remap' (needs vision) from 'text present, just not
co-located / different wording' (needs a wider text-based search)."""
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

TARGETS = [
    ("KR0005", "2024.4Q"),
    ("KR0010", "2024.1Q"), ("KR0010", "2024.3Q"), ("KR0010", "2025.3Q"),
    ("KR0010", "2025.4Q"), ("KR0010", "2026.1Q"),
    ("KR0071", "2024.4Q"),
    ("KR0080", "2024.4Q"), ("KR0080", "2025.1Q"), ("KR0080", "2025.2Q"),
    ("KR0080", "2025.3Q"), ("KR0080", "2025.4Q"), ("KR0080", "2026.1Q"),
    ("KR0087", "2026.1Q"),
    ("KR0097", "2024.2Q"),
    ("KR1098", "2024.2Q"), ("KR1098", "2024.3Q"), ("KR1098", "2024.4Q"),
]

for code, q in TARGETS:
    pdf = T2._pdf(T2.q2p(q), code)
    print(f"\n########## {code} {q}  pdf={pdf.name if pdf else None}")
    if pdf is None:
        print("  NO PDF")
        continue
    doc = fitz.open(pdf)
    n = doc.page_count
    texts = [doc[i].get_text() for i in range(n)]
    total_chars = sum(len(t) for t in texts)
    has_hd = [i for i, t in enumerate(texts) if "경과조치" in t and "적용" in t]
    has_gt = [i for i, t in enumerate(texts) if "공통적용" in t]
    has_bw = [i for i, t in enumerate(texts) if "보완자본" in t]
    has_hd2 = [i for i, t in enumerate(texts) if "한도" in t]
    has_ji = [i for i, t in enumerate(texts) if "지급여력금액" in t]
    print(f"  pages={n} total_chars={total_chars} avg={total_chars/max(n,1):.1f}/p")
    print(f"  pages with '경과조치'+'적용' = {has_hd[:8]}{'...' if len(has_hd)>8 else ''} (n={len(has_hd)})")
    print(f"  pages with '공통적용' = {has_gt[:8]} (n={len(has_gt)})")
    print(f"  pages with '보완자본' = {has_bw[:8]} (n={len(has_bw)})")
    print(f"  pages with '한도'     = {has_hd2[:8]}{'...' if len(has_hd2)>8 else ''} (n={len(has_hd2)})")
    print(f"  pages with '지급여력금액' = {has_ji[:8]}{'...' if len(has_ji)>8 else ''} (n={len(has_ji)})")
    # sample a page with 공통적용 (if any) to see raw text density
    if has_gt:
        pi = has_gt[0]
        print(f"  sample page(0idx={pi}) char_len={len(texts[pi])}")
        print(f"  sample text[:300]={texts[pi][:300]!r}")
    doc.close()
