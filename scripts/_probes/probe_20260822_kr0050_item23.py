# -*- coding: utf-8 -*-
"""Read-only probe: check KR0050 core item2/item3 (기본자본/보완자본, non-TFI) vs item50/51
   across quarters -- to see if they coincide for this always-전후동일 company (context only,
   NOT used to backfill anything)."""
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

by_q: dict[str, dict[int, dict]] = {}
for r in rows:
    q = r["공시분기"]
    it = int(r["항목번호"])
    by_q.setdefault(q, {})[it] = r

print("=== item2(기본자본, 핵심)/item3(보완자본, 핵심) vs item50/51(TFI표) ===")
for q in sorted(by_q):
    items = by_q[q]
    def v(it, key="값"):
        r = items.get(it)
        return None if r is None else r.get(key)
    print(f"  {q}: item2={v(2)!r} item3={v(3)!r}  ||  item50={v(50)!r} item51={v(51)!r}  "
          f"item1={v(1)!r}")
