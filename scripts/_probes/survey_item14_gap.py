from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent.parent
data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))

APPLIERS = frozenset({
    "KR0070", "KR0071", "KR0072", "KR0073", "KR0076", "KR0082",
    "KR0083", "KR0097", "KR0100", "KR1010", "KR1011", "KR0104",
    "KR0049", "KR0002", "KR0003", "KR0004", "KR0005", "KR0032",
})


def num(v):
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


by_cq: dict[tuple[str, str], dict[int, dict]] = {}
name_of: dict[str, str] = {}
for r in data:
    c, q, n = r["원보험사코드"], r["공시분기"], r["항목번호"]
    by_cq.setdefault((c, q), {})[n] = r
    name_of[c] = r.get("원수사명", c)

buckets = Counter()
missing14post = 0
rows = []
for (c, q), items in by_cq.items():
    if c in APPLIERS:
        continue
    r14 = items.get(14)
    if r14 is None:
        continue
    v14, vp14 = num(r14.get("값")), num(r14.get("값_적용후"))
    if vp14 is None:
        missing14post += 1
        continue
    d14 = abs(v14 - vp14) if v14 is not None else None
    if d14 is None:
        continue
    rows.append((c, q, name_of[c], d14))
    if d14 == 0:
        buckets["0 exact"] += 1
    elif d14 < 0.5:
        buckets["<0.5"] += 1
    elif d14 < 2:
        buckets["0.5-2"] += 1
    elif d14 < 10:
        buckets["2-10"] += 1
    else:
        buckets[">=10"] += 1

print(f"non-applier (company,quarter) with item14_후 missing entirely: {missing14post}")
print(f"non-applier pairs with item14 both present: {len(rows)}")
print("item14 |전-후| histogram:")
for k in ["0 exact", "<0.5", "0.5-2", "2-10", ">=10"]:
    print(f"  {k}: {buckets.get(k,0)}")

print("\nnon-exact but small (<0.5) diffs -- inspect for rounding-noise pattern:")
for c, q, name, d14 in sorted(rows, key=lambda x: x[3]):
    if 0 < d14 < 0.5:
        print(f"  {name}({c}) {q}: d14={d14:.4f}")

print("\nmid-range (0.5-10) diffs -- could be genuine small TFI effect on item14 itself:")
for c, q, name, d14 in sorted(rows, key=lambda x: x[3]):
    if 0.5 <= d14 < 10:
        print(f"  {name}({c}) {q}: d14={d14:.4f}")

print("\n>=10 outlier(s):")
for c, q, name, d14 in rows:
    if d14 >= 10:
        print(f"  {name}({c}) {q}: d14={d14:.4f}")
