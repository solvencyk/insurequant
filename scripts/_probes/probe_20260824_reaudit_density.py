# -*- coding: utf-8 -*-
"""Read-only: per-file text-density census + keyword sweep, so that a zero keyword hit is
never mistaken for 'the source does not contain it' (repo has mis-called that 3 times)."""
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "validation" / "reaudit_20260824_density.txt"

FILES = [
    "data/disclosure/FY2025_Q1/raw/KR0094_신한라이프생명보험.pdf",
    "data/disclosure/FY2025_Q3/raw/KR0094_신한라이프생명보험.pdf",
    "data/disclosure/FY2026_Q1/raw/KR0094_신한라이프생명보험.pdf",
    "data/disclosure/FY2025_Q2/raw/KR0094_신한라이프생명보험.pdf",
]
KWS = ["금리위험액현황", "시장위험", "순자산가치", "금리위험액", "충격전", "평균회귀",
       "주식위험액현황", "금리위험"]

buf = []
for rel in FILES:
    p = ROOT / rel
    if not p.exists():
        buf.append("MISSING %s" % rel)
        continue
    doc = fitz.open(p)
    texts = [doc[i].get_text() for i in range(doc.page_count)]
    total = sum(len(t) for t in texts)
    empties = sum(1 for t in texts if len(t.strip()) < 50)
    buf.append("=" * 88)
    buf.append("%s" % rel)
    buf.append("  pages=%d  total_chars=%d  mean_chars/page=%.0f  pages_with_<50_chars=%d"
               % (doc.page_count, total, total / max(doc.page_count, 1), empties))
    for kw in KWS:
        hits = [i + 1 for i, t in enumerate(texts) if kw in t.replace(" ", "")]
        buf.append("  %-14s hits=%-4d pages=%s" % (kw, len(hits), hits[:14]))
    doc.close()

OUT.write_text("\n".join(buf), encoding="utf-8")
print("wrote", OUT)
