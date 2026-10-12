"""Read-only: summarize data/dart/viz/bs_manual_overrides.json cells (keys, source tags) and the part for 4Q main items."""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parents[3]
d = json.loads((ROOT / "data/dart/viz/bs_manual_overrides.json").read_text(encoding="utf-8"))
cells = d["cells"]
k0 = next(iter(cells))
print("sample", k0, json.dumps(cells[k0], ensure_ascii=False)[:300])
keys = Counter()
tags = Counter()
for k, v in cells.items():
    for kk in v:
        keys[kk] += 1
    n = str(v.get("note") or v.get("why") or v.get("source") or "")[:40]
    tags[n] += 1
print("field counts", dict(keys))
for t, c in tags.most_common(25):
    print(c, repr(t))
main = {1, 2, 3, 4, 14, 20, 21, 30, 31}
sel = [k for k in cells if int(k.split("|")[1]) in main and k.split("|")[2].endswith("4Q")]
print("overlay cells on 4Q main items:", len(sel))
