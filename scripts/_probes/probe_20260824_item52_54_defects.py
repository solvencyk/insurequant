# -*- coding: utf-8 -*-
"""Read-only probe: dump current live rows for the buckets named in
inbox/parser/20260824T0400Z__validation__MULTI__item52_54_load_defects.md (A-G).
"""
from __future__ import annotations
import json
import sys
import os
from pathlib import Path

sys.stdout = os.fdopen(1, "w", encoding="utf-8", closefd=False)

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "kics_disclosure.json"

data = json.loads(TARGET.read_text(encoding="utf-8"))
print(f"row_count = {len(data):,}")

BUCKETS = [
    ("KR1098", "2023.1Q", [50, 52]),
    ("KR1098", "2023.2Q", [50, 52]),
    ("KR1098", "2023.3Q", [50, 52]),
    ("KR1098", "2023.4Q", [50, 52]),
    ("KR1098", "2024.1Q", [50, 52]),
    ("KR0008", "2025.3Q", [1, 14, 50, 51, 52]),
    ("KR0104", "2024.3Q", [51, 53, 54]),
    ("KR0083", "2024.3Q", [47, 48, 49, 53, 54]),
    ("KR0003", "2026.1Q", [53, 54]),
    ("KR0087", "2024.1Q", [53, 54]),
    ("KR0097", "2025.2Q", [53, 54]),
    ("KR0100", "2023.1Q", [53, 54]),  # inbox-B chubb, opportunistic check
    ("KR0087", "2024.3Q", [53, 54]),  # inbox-F dongyang unconfirmed
]

for code, q, items in BUCKETS:
    print(f"\n=== {code} {q} ===")
    for it in items:
        rows = [r for r in data if r.get("원보험사코드") == code and r.get("공시분기") == q and int(r.get("항목번호", -1)) == it]
        if not rows:
            print(f"  item{it}: (없음)")
        for r in rows:
            print(f"  item{it}: 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r} 항목명={r.get('항목명')!r}")
