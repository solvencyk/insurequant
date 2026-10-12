"""Read-only: list the blocks of an extracted_history *_measurement.json (caption, type, size, first rows).

usage: python s07_peek_blocks.py <canonical> <quarter> [--rows 6] [--grep 기초]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]
a = sys.argv[1:]
canon, q = a[0], a[1]
nrows = 6
grep = None
if "--rows" in a:
    nrows = int(a[a.index("--rows") + 1])
if "--grep" in a:
    grep = a[a.index("--grep") + 1]
p = ROOT / "data/dart/extracted_history" / f"{canon}__{q}_measurement.json"
d = json.loads(p.read_text(encoding="utf-8"))
print(p.name, "blocks", len(d))
print("block keys", list(d[0].keys()))
for i, b in enumerate(d):
    cap = (b.get("caption") or "")[:110]
    rows = b.get("rows") or []
    hdr = b.get("header") or []
    if grep and grep not in json.dumps(b, ensure_ascii=False):
        continue
    print(f"--- [{i}] type={b.get('block_type')} line={b.get('line_no')} nrows={len(rows)} hdr_rows={len(hdr)} score={b.get('score')} cap={cap}")
    for h in hdr[:3]:
        print("   H:", json.dumps(h, ensure_ascii=False)[:230])
    for r in rows[:nrows]:
        print("   R:", json.dumps(r, ensure_ascii=False)[:230])
