# -*- coding: utf-8 -*-
"""tier2 추출값을 손검증한 4개 사례와 직접 대조."""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from fix_20260821_tier2_limit_lines import _pdf, extract_tier2, q2p  # noqa: E402

CASES = [
    ("KR0100", "2024.4Q", {47: (6399, 6399), 48: (69861, 69861), 49: (143248, 143248)}),
    ("KR0083", "2026.1Q", {47: (1040999, 651058), 48: (696260, 696260), 49: (None, None)}),
    ("KR1011", "2026.1Q", {47: (440535, 280056), 48: (359792, 359792), 49: (340742, 340742)}),
    ("KR0104", "2025.1Q", {47: (1565022, 1315022), 48: (1374563, 1374563), 49: (2862433, 2862433)}),
]

for c, q, expect in CASES:
    pdf = _pdf(q2p(q), c)
    found, reason = extract_tier2(pdf)
    print(f"{c} {q}: reason={reason}")
    for it in (47, 48, 49):
        got = found.get(it)
        exp = expect[it]
        ok = "OK" if got == exp or (got is None and exp == (None, None)) else "MISMATCH"
        print(f"  item{it}: 추출={got}  기대(백만원)={exp}  {ok}")
