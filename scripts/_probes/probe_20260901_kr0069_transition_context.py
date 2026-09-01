# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
t = (REPO / "md_inbox" / "FY2026_Q2" / "KR0069_삼성생명.md").read_text(encoding="utf-8")
lines = t.splitlines()
for i, l in enumerate(lines):
    if "경과조치" in l:
        lo, hi = max(0, i - 2), min(len(lines), i + 3)
        print(f"--- around line {i+1} ---")
        for j in range(lo, hi):
            print(j + 1, lines[j])
        print()
