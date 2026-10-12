# -*- coding: utf-8 -*-
"""Read-only: DART 엠지손해보험 FY2025 (rcept 20260406003175) tables that have a 보험계약마진 column and 기초/기말 순장부금액 rows."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant")
from pathlib import Path
from src.ifrs17.csm_extractor import _iter_tables_with_context
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/dart/FY2025_Q4/raw/KR0004_엠지손해보험_20260406003175/20260406003175_00760.xml")
n = 0
for t in _iter_tables_with_context(p):
    hdr = " ".join(c for r in t.header for c in r)
    first = [r[0] for r in t.rows if r]
    body = " ".join(first)
    if "보험계약마진" in hdr + " ".join(" ".join(r) for r in t.rows[:2]) and ("기말" in body and "기초" in body) and ("계약이전" in body or "신계약" in body or "상각" in body):
        n += 1
        print("=" * 110)
        print("line", t.line_no, "caption:", t.caption[:140])
        print("header:", t.header)
        for r in t.rows:
            print("   ", r)
print("tables", n)
