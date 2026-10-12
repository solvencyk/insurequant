"""Read-only: list IFRS17_BS.json items (number, name, row count) and the quarters/companies covered."""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]
d = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
print("rows", len(d), "keys", list(d[0].keys()))
items = defaultdict(lambda: [None, 0])
for r in d:
    it = items[r["항목번호"]]
    it[0] = r["항목명"]
    it[1] += 1
for k in sorted(items):
    print(k, items[k])
print("quarters", sorted({r["공시분기"] for r in d}))
print("sample", json.dumps(d[0], ensure_ascii=False))
