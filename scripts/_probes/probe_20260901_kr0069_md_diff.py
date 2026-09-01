# -*- coding: utf-8 -*-
"""Diff old vs new KR0069 2026.2Q MD: which headers/sections were gained vs lost.
Read-only comparison of two on-disk MD files (no writes)."""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
old = (REPO / "md_inbox" / "FY2026_Q2" / "KR0069_삼성생명.md.bak_20260901_marketgap").read_text(encoding="utf-8")
new = (REPO / "md_inbox" / "FY2026_Q2" / "KR0069_삼성생명.md").read_text(encoding="utf-8")


def headers(text):
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("## ") or re.match(r"^\d+\)", s):
            out.append(s)
    return out


ho = headers(old)
hn = headers(new)
so, sn = set(ho), set(hn)
print(f"old headers: {len(ho)} (unique {len(so)})  new headers: {len(hn)} (unique {len(sn)})")
print(f"\n=== LOST (in old, not in new) === ({len(so - sn)})")
for h in ho:
    if h in (so - sn):
        print(" -", h)
print(f"\n=== GAINED (in new, not in old) === ({len(sn - so)})")
for h in hn:
    if h in (sn - so):
        print(" +", h)
