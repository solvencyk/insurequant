"""Probe: item14-23 값/값_적용후 for the 5 companies flagged in inbox/parser/20260715T0801Z at 2026.1Q."""
from __future__ import annotations

import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent.parent
data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))

TARGETS = ["KR0068", "KR0073", "KR0097", "KR0003", "KR0104"]
QUARTER = "2026.1Q"
ITEMS = list(range(1, 29))

by_key: dict[tuple[str, int], dict] = {}
for r in data:
    if r["원보험사코드"] in TARGETS and r["공시분기"] == QUARTER:
        by_key[(r["원보험사코드"], r["항목번호"])] = r

for code in TARGETS:
    name = None
    print(f"=== {code} ===")
    for item_no in ITEMS:
        row = by_key.get((code, item_no))
        if row is None:
            print(f"  item{item_no}: <no row>")
            continue
        name = row.get("원수사명")
        v = row.get("값")
        vp = row.get("값_적용후", "<absent-key>")
        print(f"  item{item_no} ({row.get('항목명','')[:20]}): 값={v}  값_적용후={vp}")
    print(f"  name={name}")
