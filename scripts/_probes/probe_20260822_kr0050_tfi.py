# -*- coding: utf-8 -*-
"""Read-only probe: KR0050 (하나손해보험) item47/48/49/50/51 coverage across quarters,
   plus item1/item14 anchors. No writes anywhere."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"

data = json.loads(TARGET.read_text(encoding="utf-8"))
rows = [r for r in data if r.get("원보험사코드") == "KR0050"]
print(f"KR0050 총 레코드 = {len(rows)}")

by_q: dict[str, dict[int, dict]] = {}
for r in rows:
    q = r["공시분기"]
    it = int(r["항목번호"])
    by_q.setdefault(q, {})[it] = r

print(f"분기 목록 ({len(by_q)}개): {sorted(by_q)}")
print()
print("=== 항목 1/14/27/47/48/49/50/51 커버리지 (분기별) ===")
for q in sorted(by_q):
    items = by_q[q]
    def fmt(it):
        r = items.get(it)
        if r is None:
            return "결측"
        v = r.get("값")
        vp = r.get("값_적용후")
        return f"전={v} 후={vp}"
    print(f"  {q}: item1({fmt(1)}) item14({fmt(14)})")
    for it in (47, 48, 49, 50, 51):
        if it in items:
            print(f"        item{it} 항목명={items[it].get('항목명')!r} {fmt(it)}")

print()
print("=== 47/48/49/50/51 중 하나라도 있는 분기 요약 ===")
any_found = False
for q in sorted(by_q):
    present = [it for it in (47, 48, 49, 50, 51) if it in by_q[q]]
    if present:
        any_found = True
        print(f"  {q}: {present}")
if not any_found:
    print("  (없음 -- KR0050 전체 분기에 47/48/49/50/51 전부 결측)")
