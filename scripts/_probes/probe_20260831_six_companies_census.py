# -*- coding: utf-8 -*-
"""Census probe: item counts for the 6 target companies, 2026.1Q vs 2026.2Q, in root kics_disclosure.json."""
import json
import sys
import io
from pathlib import Path
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
MASTER = ROOT / "kics_disclosure.json"

TARGETS = ["KR0069", "KR0070", "KR0082", "KR0001", "KR0073", "KR1011"]

rows = json.loads(MASTER.read_text(encoding="utf-8"))
print(f"total rows in master: {len(rows)}")

by_co_q = defaultdict(list)
for r in rows:
    co = r.get("원보험사코드")
    q = r.get("공시분기")
    by_co_q[(co, q)].append(r)

for co in TARGETS:
    name = None
    for q in ["2025.4Q", "2026.1Q", "2026.2Q"]:
        recs = by_co_q.get((co, q), [])
        if recs:
            name = recs[0].get("원수사명")
        items = sorted(set(r["항목번호"] for r in recs))
        print(f"{co} {name!r:20s} {q}: n_rows={len(recs)} n_items={len(items)} items={items}")
    print()
