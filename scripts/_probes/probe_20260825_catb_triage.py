# -*- coding: utf-8 -*-
"""CAT B (item50/51/52 all absent, 30 buckets) triage -- is the TFI table genuinely
absent from raw, or just never-attempted (whole 47-54 backlog gap)? Read-only."""
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

# KR0079 all 13, KR1010 all 12, plus KR0097 2024.4Q (already documented separately)
TARGETS = [("KR0079", q) for q in
           ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q",
            "2024.4Q","2025.1Q","2025.2Q","2025.3Q","2025.4Q","2026.1Q"]] + \
          [("KR1010", q) for q in
           ["2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q",
            "2025.1Q","2025.2Q","2025.3Q","2025.4Q","2026.1Q"]]

for code, q in TARGETS:
    pdf = T2._pdf(T2.q2p(q), code)
    if pdf is None:
        print(f"{code} {q}: NO PDF")
        continue
    doc = fitz.open(pdf)
    n = doc.page_count
    texts = [doc[i].get_text() for i in range(n)]
    total_chars = sum(len(t) for t in texts)
    has_gt = sum(1 for t in texts if "공통적용" in t)
    has_bw = sum(1 for t in texts if "보완자본" in t)
    has_ji = sum(1 for t in texts if "지급여력금액" in t)
    has_hj = sum(1 for t in texts if "경과조치" in t)
    print(f"{code} {q}: pages={n} chars={total_chars} avg={total_chars/max(n,1):.1f}/p "
          f"공통적용={has_gt} 보완자본={has_bw} 지급여력금액={has_ji} 경과조치={has_hj}  pdf={pdf.name}")
    doc.close()
