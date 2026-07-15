"""Round 2: check items 1-28 for KR0068 (2024.3Q/2025.2Q/2025.3Q) and
KR0104 (2023.1Q/2023.2Q) -- same shape as the round-1 2026.1Q gap?"""
from __future__ import annotations

import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent.parent
data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))

TARGETS = [
    ("KR0068", "2024.3Q"),
    ("KR0068", "2025.2Q"),
    ("KR0068", "2025.3Q"),
    ("KR0104", "2023.1Q"),
    ("KR0104", "2023.2Q"),
]
ITEMS = list(range(1, 29))

by_key: dict[tuple[str, str, int], dict] = {}
for r in data:
    key = (r["원보험사코드"], r["공시분기"])
    if key in TARGETS:
        by_key[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r

for code, q in TARGETS:
    name = None
    print(f"=== {code} {q} ===")
    for item_no in ITEMS:
        row = by_key.get((code, q, item_no))
        if row is None:
            print(f"  item{item_no}: <no row>")
            continue
        name = row.get("원수사명")
        v = row.get("값")
        vp = row.get("값_적용후", "<absent-key>")
        print(f"  item{item_no} ({row.get('항목명','')[:18]}): 값={v}  값_적용후={vp}")
    print(f"  name={name}")
