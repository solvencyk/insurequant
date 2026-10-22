#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 12: for KR0071 (and as a control KR0094, KR0070) find the lines that explain the comparative restatement (일탈회계 / 계약자지분조정 / 소급 / 재작성) -> stdout + s12_cause_lines.txt"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e20_xml as X  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
JOBS = [("KR0071", "FY2026_Q1"), ("KR0071", "FY2026_Q2"), ("KR0094", "FY2026_Q2"), ("KR0094", "FY2026_Q1")]
KEY = re.compile(r"일탈회계|계약자지분조정|소급")
L = []
for code, fy in JOBS:
    try:
        p = X.main_xml(code, fy)
    except FileNotFoundError:
        continue
    lines = X.load_lines(p)
    L.append(f"##### {code} {fy} {X.rel(p)}")
    n = 0
    for i, l in enumerate(lines, 1):
        t = re.sub(r"\s+", " ", X.RE_TAG.sub("", l)).strip()
        if len(t) > 30 and KEY.search(t):
            L.append(f"  L{i}: {t[:420]}")
            n += 1
            if n >= 14:
                break
    if n == 0:
        L.append("  (none)")
(HERE / "s12_cause_lines.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
print("\n".join(L))
