# -*- coding: utf-8 -*-
"""Dump KR0071 items 1-28 across 2024.3Q/2024.4Q/2025.1Q, both 값 and 값_적용후."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
records = data if isinstance(data, list) else data.get("records") or data.get("rows") or []

CODE = "KR0071"
QUARTERS = ["2024.3Q", "2024.4Q", "2025.1Q"]

by_item = {}
for r in records:
    if r.get("원보험사코드") != CODE:
        continue
    q = r.get("공시분기")
    if q not in QUARTERS:
        continue
    try:
        it = int(r.get("항목번호"))
    except (TypeError, ValueError):
        continue
    if not (1 <= it <= 28):
        continue
    by_item.setdefault(it, {})[q] = (r.get("값"), r.get("값_적용후"), r.get("항목명"))

for it in sorted(by_item):
    row = by_item[it]
    label = None
    parts = []
    for q in QUARTERS:
        if q in row:
            v, vp, lbl = row[q]
            label = label or lbl
            parts.append(f"{q}: 값={v!r} 값_적용후={vp!r}")
        else:
            parts.append(f"{q}: (no row)")
    print(f"item{it:>2} [{label}]")
    for p in parts:
        print(f"    {p}")
