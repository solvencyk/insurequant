#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 11: find the restatement explanation text in each later filing (lines that mention 재작성/오류/정정 together with 비교/소급/전기) -> s11_restate_notes.txt (read-only)"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e20_xml as X  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
JOBS = [("KR0087", "FY2025_Q4"), ("KR0087", "FY2026_Q1"), ("KR0087", "FY2026_Q2"), ("KR0104", "FY2025_Q4"), ("KR0104", "FY2026_Q1"), ("KR0104", "FY2026_Q2"),
        ("KR0069", "FY2026_Q1"), ("KR0069", "FY2026_Q2"), ("KR0094", "FY2026_Q2"), ("KR0070", "FY2026_Q1"), ("KR0070", "FY2026_Q2"), ("KR0072", "FY2025_Q4"),
        ("KR0068", "FY2025_Q4"), ("KR0068", "FY2026_Q1"), ("KR0068", "FY2026_Q2"), ("KR0071", "FY2026_Q1"), ("KR0071", "FY2026_Q2"),
        ("KR0032", "FY2024_Q1"), ("KR0082", "FY2024_Q1"), ("KR0083", "FY2025_Q3")]
KEY = re.compile(r"재작성|전기오류|오류수정|오류의 수정|비교재무제표")
L = []
for code, fy in JOBS:
    p = X.main_xml(code, fy)
    lines = X.load_lines(p)
    L.append(f"##### {code} {fy} {X.rel(p)}")
    n = 0
    for i, l in enumerate(lines, 1):
        t = re.sub(r"\s+", " ", X.RE_TAG.sub("", l)).strip()
        if len(t) > 40 and KEY.search(t) and re.search(r"회계정책|오류|계약자|소급|변경|정정|수정", t):
            L.append(f"  L{i}: {t[:520]}")
            n += 1
            if n >= 6:
                break
    if n == 0:
        L.append("  (no matching line)")
(HERE / "s11_restate_notes.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
print(len(L))
