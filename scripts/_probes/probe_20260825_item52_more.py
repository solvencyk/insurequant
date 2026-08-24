# -*- coding: utf-8 -*-
"""Wider diagnostic: KR0100 2023.1Q (2-column merge suspect), KR0087 3 buckets
(candidate-page +1 logic), KR0009 2025.1Q value-row split confirm, KR0068 other
quarters spot-check.
"""
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
import fix_20260824_tfi_capital_memo_rows as M  # noqa: E402


def dump(code, q, pad_before=20, pad_after=3):
    pdf = T2._pdf(T2.q2p(q), code)
    print(f"\n########## {code} {q}  pdf={pdf}")
    if pdf is None:
        print("  NO PDF")
        return
    doc = fitz.open(pdf)
    texts = [doc[i].get_text() for i in range(doc.page_count)]
    matched = [i for i, t in enumerate(texts)
               if "공통적용" in t and "보완자본" in t and "한도" in t]
    candidates = list(dict.fromkeys(matched + [i + 1 for i in matched if i + 1 < len(texts)]))
    print(f"  matched={matched} candidates={candidates}")
    for pi in candidates:
        words = doc[pi].get_text("words")
        rows = M._cluster_rows(words)
        idx48 = next((i for i, (_y, tok) in enumerate(rows) if M._label_norm(tok) == "보완자본한도"), None)
        print(f"  --- page(0idx={pi}, 1idx={pi+1}) idx48={idx48} n_rows={len(rows)}")
        if idx48 is None:
            # dump everything so we can see what's going on
            for i, (y, tok) in enumerate(rows):
                lbl = M._label_norm(tok)
                raw_txt = " | ".join(f"({x0:.1f},{x1:.1f}){t}" for x0, x1, t in tok)
                print(f"    row[{i}] y={y:.1f} label_norm={lbl!r}")
                print(f"        raw: {raw_txt}")
            continue
        lo = max(0, idx48 - pad_before)
        for i in range(lo, min(len(rows), idx48 + pad_after)):
            y, tok = rows[i]
            lbl = M._label_norm(tok)
            raw_txt = " | ".join(f"({x0:.1f},{x1:.1f}){t}" for x0, x1, t in tok)
            print(f"    row[{i}] y={y:.1f} label_norm={lbl!r}")
            print(f"        raw: {raw_txt}")
    doc.close()


dump("KR0100", "2023.1Q", pad_before=25, pad_after=2)
dump("KR0087", "2023.2Q")
dump("KR0087", "2025.1Q")
dump("KR0087", "2025.4Q")
dump("KR0009", "2025.1Q")
dump("KR0068", "2024.2Q")
dump("KR0068", "2024.3Q")
