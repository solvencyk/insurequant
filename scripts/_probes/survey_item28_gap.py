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

rows = []
for (c, q), items in by_cq.items():
    if c in APPLIERS:
        continue
    r27, r28 = items.get(27), items.get(28)
    if r27 is None or r28 is None:
        continue
    v27, vp27 = num(r27.get("값")), num(r27.get("값_적용후"))
    v28, vp28 = num(r28.get("값")), num(r28.get("값_적용후"))
    if None in (v27, vp27, v28, vp28):
        continue
    d27, d28 = abs(v27 - vp27), abs(v28 - vp28)
    rows.append((c, q, name_of[c], d27, d28))

# cases where item27 is tiny-safe (<0.05) but item28 is NOT (>=0.05)
print("item27 safe(<0.05) but item28 NOT safe(>=0.05):")
for c, q, name, d27, d28 in sorted(rows, key=lambda x: -x[4]):
    if d27 < 0.05 and d28 >= 0.05:
        print(f"  {name}({c}) {q}: d27={d27:.4f} d28={d28:.4f}")

buckets28 = Counter()
for c, q, name, d27, d28 in rows:
    if d28 == 0:
        buckets28["0 exact"] += 1
    elif d28 < 0.05:
        buckets28["<0.05"] += 1
    elif d28 < 0.5:
        buckets28["0.05-0.5"] += 1
    elif d28 < 2:
        buckets28["0.5-2"] += 1
    else:
        buckets28[">=2"] += 1
print("\nitem28 |전-후| histogram:")
for k in ["0 exact", "<0.05", "0.05-0.5", "0.5-2", ">=2"]:
    print(f"  {k}: {buckets28.get(k,0)}")
