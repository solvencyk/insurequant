"""Read-only: summarize pl_tier1_scan.csv (RESTATED_STALE etc.) by item / by company / relative size."""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(HERE / "pl_tier1_scan.csv", encoding="utf-8-sig")))
st = [r for r in rows if r["cls"] == "RESTATED_STALE"]
print("RESTATED_STALE cells", len(st))
by_item = Counter(r["item"] for r in st)
print("by item", dict(sorted(by_item.items(), key=lambda kv: int(kv[0]))))
by_q = Counter(r["quarter"] for r in st)
print("by quarter", dict(sorted(by_q.items())))
by_c = Counter(r["kr"] + " " + r["name"] for r in st)
print("by company", dict(sorted(by_c.items())))


def rel(r):
    try:
        m, l = float(r["master"]), float(r["later"])
    except Exception:
        return None
    base = max(abs(m), abs(l), 1e-9)
    return abs(m - l) / base


big = [r for r in st if (rel(r) or 0) > 0.01]
print("rel>1%:", len(big), " rel>10%:", len([r for r in st if (rel(r) or 0) > 0.1]))
print("---- sample large")
for r in sorted(big, key=lambda r: -(rel(r) or 0))[:40]:
    print(r["kr"], r["name"][:6], r["quarter"], "item", r["item"], "master", r["master"][:12], "later", r["later"][:12], "rel", round(rel(r), 3))
print("---- other classes")
for c in ("MASTER_NEQ_ORIG", "RESTATED_ADOPTED", "ONLY_LATER"):
    sub = [r for r in rows if r["cls"] == c]
    print(c, len(sub))
    for r in sub[:30]:
        print("  ", r["kr"], r["name"][:6], r["quarter"], "item", r["item"], "master", r["master"][:12], "orig", r["orig"][:12], "later", r["later"][:12])
