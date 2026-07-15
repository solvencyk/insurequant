from __future__ import annotations

import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent.parent
data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))

TARGETS = [
    ("KR0069", "2025.1Q"),
    ("KR0087", "2024.2Q"),
    ("KR0087", "2024.4Q"),
    ("KR0087", "2025.1Q"),
    ("KR0097", "2024.4Q"),
]
ITEMS = list(range(14, 29))

by_key: dict[tuple[str, str, int], dict] = {}
for r in data:
    key = (r["원보험사코드"], r["공시분기"])
    if key in TARGETS:
        by_key[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r

for code, q in TARGETS:
    print(f"=== {code} {q} ===")
    for item_no in ITEMS:
        row = by_key.get((code, q, item_no))
        if row is None:
            print(f"  item{item_no}: <no row>")
            continue
        v = row.get("값")
        vp = row.get("값_적용후", "<absent-key>")
        print(f"  item{item_no}: 값={v}  값_적용후={vp}")
