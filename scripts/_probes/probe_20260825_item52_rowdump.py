# -*- coding: utf-8 -*-
"""Diagnose why the item52 headline-capital row match fails for CAT-A buckets
(50/51 present, 52 absent). Dumps _cluster_rows()/_label_norm() output around
idx48 for a handful of buckets, read-only.
"""
from __future__ import annotations
import sys
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout = os.fdopen(1, "w", encoding="utf-8", closefd=False)

import fitz  # noqa: E402
fitz.TOOLS.mupdf_display_errors(False)
fitz.TOOLS.mupdf_display_warnings(False)

import fix_20260821_tier2_limit_lines as T2  # noqa: E402
import fix_20260824_tfi_capital_memo_rows as M  # noqa: E402

TARGETS = [
    ("KR0004", "2025.1Q"),
    ("KR0068", "2023.4Q"),
    ("KR0087", "2023.2Q"),
    ("KR0100", "2023.1Q"),
    ("KR0009", "2025.1Q"),
]

for code, q in TARGETS:
    pdf = T2._pdf(T2.q2p(q), code)
    print(f"\n########## {code} {q}  pdf={pdf}")
    if pdf is None:
        print("  NO PDF")
        continue
    doc = fitz.open(pdf)
    texts = [doc[i].get_text() for i in range(doc.page_count)]
    matched = [i for i, t in enumerate(texts)
               if "공통적용" in t and "보완자본" in t and "한도" in t]
    print(f"  matched pages (0idx) = {matched}")
    for pi in matched[:2]:
        words = doc[pi].get_text("words")
        rows = M._cluster_rows(words)
        idx48 = next((i for i, (_y, tok) in enumerate(rows) if M._label_norm(tok) == "보완자본한도"), None)
        print(f"  page(0idx={pi}) idx48={idx48}  n_rows={len(rows)}")
        if idx48 is None:
            continue
        lo = max(0, idx48 - 10)
        for i in range(lo, min(len(rows), idx48 + 2)):
            y, tok = rows[i]
            lbl = M._label_norm(tok)
            raw_txt = " | ".join(f"({x0:.1f},{x1:.1f}){t}" for x0, x1, t in tok)
            print(f"    row[{i}] y={y:.1f} label_norm={lbl!r}")
            print(f"        raw: {raw_txt}")
    doc.close()
