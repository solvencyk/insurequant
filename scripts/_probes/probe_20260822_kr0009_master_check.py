# -*- coding: utf-8 -*-
"""probe_20260822_kr0009_master_check.py -- read-only. Confirm master state for
KR0009/2023.1Q: item1/14 pre=post anchors, and item47-51 presence/absence."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json")
data = json.loads(TARGET.read_text(encoding="utf-8"))

rows = [r for r in data if r.get("원보험사코드") == "KR0009" and r.get("공시분기") == "2023.1Q"]
print(f"KR0009 / 2023.1Q rows in master: {len(rows)}")
by_item = {int(r["항목번호"]): r for r in rows}
for it in sorted(by_item):
    r = by_item[it]
    print(f"  item{it:>2} {r.get('항목명','')[:30]:<30} 값={r.get('값')!r}  값_적용후={r.get('값_적용후')!r}")

print()
for it in (47, 48, 49, 50, 51):
    print(f"  item{it} present: {it in by_item}")
