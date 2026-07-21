"""Survey: for every (company, quarter) NOT in the 18-applier list, how do
item27/item28 전/후 compare, and how many sub-item cells are currently
blank? Used to calibrate a safe tolerance for a comprehensive mirror sweep.
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

# for non-appliers: compare item27/28 pre vs post, bucket by |diff|
diffs27 = []
diffs28 = []
both_missing = 0
one_missing = 0
both_present_equal_exact = 0
per_cq_status: dict[tuple[str, str], str] = {}

for (c, q), items in by_cq.items():
    if c in APPLIERS:
        continue
    r27 = items.get(27)
    r28 = items.get(28)
    if r27 is None:
        continue
    v27, vp27 = num(r27.get("값")), num(r27.get("값_적용후"))
    v28, vp28 = (num(r28.get("값")), num(r28.get("값_적용후"))) if r28 else (None, None)
    if vp27 is None:
        one_missing += 1
        per_cq_status[(c, q)] = "post27_missing"
        continue
    d27 = abs(v27 - vp27) if v27 is not None else None
    d28 = abs(v28 - vp28) if (v28 is not None and vp28 is not None) else None
    diffs27.append(d27)
    if d28 is not None:
        diffs28.append(d28)
    per_cq_status[(c, q)] = f"d27={d27}"

# histogram buckets for d27
buckets = Counter()
for d in diffs27:
    if d is None:
        buckets["None"] += 1
    elif d == 0:
        buckets["0 exact"] += 1
    elif d < 0.005:
        buckets["<0.005"] += 1
    elif d < 0.02:
        buckets["0.005-0.02"] += 1
    elif d < 0.05:
        buckets["0.02-0.05"] += 1
    elif d < 0.1:
        buckets["0.05-0.1"] += 1
    elif d < 0.5:
        buckets["0.1-0.5"] += 1
    elif d < 2:
        buckets["0.5-2"] += 1
    else:
        buckets[">=2"] += 1

print("item27 |전-후| histogram for NON-appliers (item27_후 present):")
for k in ["0 exact", "<0.005", "0.005-0.02", "0.02-0.05", "0.05-0.1", "0.1-0.5", "0.5-2", ">=2"]:
    print(f"  {k}: {buckets.get(k, 0)}")
print(f"non-applier (company,quarter) with item27_후 missing entirely: {one_missing}")
print(f"total non-applier (company,quarter) pairs with item27 row: {len(per_cq_status)}")

# how many cells (all items) are currently blank 값_적용후 for non-appliers where
# item27/28 diff < 0.05 (candidate safe threshold)?
candidate_safe: list[tuple[str, str]] = []
for (c, q), items in by_cq.items():
    if c in APPLIERS:
        continue
    r27 = items.get(27)
    if r27 is None:
        continue
    v27, vp27 = num(r27.get("값")), num(r27.get("값_적용후"))
    if vp27 is None or v27 is None:
        continue
    if abs(v27 - vp27) >= 0.05:
        continue
    r28 = items.get(28)
    if r28 is not None:
        v28, vp28 = num(r28.get("값")), num(r28.get("값_적용후"))
        if v28 is not None and vp28 is not None and abs(v28 - vp28) >= 0.05:
            continue
    candidate_safe.append((c, q))

blank_cells = 0
for (c, q) in candidate_safe:
    for n, row in by_cq[(c, q)].items():
        if row.get("값_적용후") in (None, "") and row.get("값") not in (None, ""):
            blank_cells += 1

print(f"\ncandidate 'safe' (company,quarter) pairs (|d27|<0.05 and |d28|<0.05 if present): {len(candidate_safe)}")
print(f"blank 값_적용후 cells within those pairs (fillable via mirror): {blank_cells}")
