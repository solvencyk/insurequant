# -*- coding: utf-8 -*-
"""Read-only: dump selected master item values for given companies."""
import json, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
recs = data["records"] if isinstance(data, dict) and "records" in data else data

CODES = sys.argv[1].split(",")
ITEMS = [str(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None

# discover key names
sample = recs[0]
print("RECORD KEYS:", list(sample.keys()))

by = {}
for r in recs:
    c = r.get("원보험사코드")
    if c not in CODES:
        continue
    q = r.get("공시분기")
    it = str(r.get("항목번호") or r.get("item") or "")
    if ITEMS and it not in ITEMS:
        continue
    by.setdefault((c, q), {})[it] = (r.get("값"), r.get("값_적용후"), r.get("항목명"))

for k in sorted(by):
    print("=" * 100)
    print(k)
    for it in sorted(by[k], key=lambda s: (len(s), s)):
        v, va, nm = by[k][it]
        print(f"  item{it:>3}  값={v!r:>16}  값_적용후={va!r:>16}  {nm}")
