# -*- coding: utf-8 -*-
"""Check whether the orphan buckets' surviving child values sit in the gold overlay
(data/_gold/user_pl_cells.json) or are unowned merge leftovers."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

g = json.load(open(ROOT / "data" / "_gold" / "user_pl_cells.json", encoding="utf-8"))
print("_doc:", json.dumps(g.get("_doc"), ensure_ascii=False)[:800])
sets = g["set"]
print("set type:", type(sets), "len:", len(sets))
sample = sets[:3] if isinstance(sets, list) else list(sets.items())[:3]
print("sample:", json.dumps(sample, ensure_ascii=False)[:800])

CODES = {"KR0002", "KR0003", "KR0004", "KR0005", "KR0029", "KR0068", "KR0069",
         "KR0071", "KR0073", "KR0074", "KR0075", "KR0083", "KR0094", "KR0095",
         "KR0097", "KR0104"}
QS = {"2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.4Q", "2025.4Q"}

print("\n=== gold entries touching orphan companies/quarters ===")
if isinstance(sets, list):
    for e in sets:
        s = json.dumps(e, ensure_ascii=False)
        if any(c in s for c in CODES) and any(q in s for q in QS):
            print(" ", s[:300])
else:
    for k, v in sets.items():
        if any(c in k for c in CODES) and any(q in k for q in QS):
            print(" ", k, "->", json.dumps(v, ensure_ascii=False)[:200])
