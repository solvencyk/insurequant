from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent.parent
data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))

APPLIERS = frozenset({
    "KR0070", "KR0071", "KR0072", "KR0073", "KR0076", "KR0082",
    "KR0083", "KR0097", "KR0100", "KR1010", "KR1011", "KR0104",
    "KR0049", "KR0002", "KR0003", "KR0004", "KR0005", "KR0032",
})
TOL14 = 1.0


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

safe_pairs = []
excluded_pairs = []
for (c, q), items in by_cq.items():
    if c in APPLIERS:
        continue
    r14 = items.get(14)
    if r14 is None:
        continue
    v14, vp14 = num(r14.get("값")), num(r14.get("값_적용후"))
    if v14 is None or vp14 is None:
        continue
    if abs(v14 - vp14) <= TOL14:
        safe_pairs.append((c, q))
    else:
        excluded_pairs.append((c, q, name_of[c], abs(v14 - vp14)))

blank_1523 = 0
blank_per_pair = {}
for (c, q) in safe_pairs:
    items = by_cq[(c, q)]
    n_blank = 0
    for n in range(15, 24):
        row = items.get(n)
        if row is None:
            continue
        if row.get("값_적용후") in (None, "") and row.get("값") not in (None, ""):
            n_blank += 1
    if n_blank:
        blank_per_pair[(c, q)] = n_blank
        blank_1523 += n_blank

print(f"safe pairs (item14 within {TOL14}): {len(safe_pairs)}")
print(f"excluded pairs (real item14 diff, must stay blank): {len(excluded_pairs)}")
for c, q, name, d in excluded_pairs:
    print(f"  EXCLUDED: {name}({c}) {q}: d14={d:.2f}")
print(f"\nfillable blank cells in items 15-23 across safe pairs: {blank_1523}")
print(f"(company,quarter) pairs with >=1 blank cell: {len(blank_per_pair)}")

# also check items 29-35 / 36-40 scope (only 2Q/4Q, gated on item17/19)
blank_2935 = 0
blank_3640 = 0
for (c, q) in safe_pairs:
    if not (q.endswith("2Q") or q.endswith("4Q")):
        continue
    items = by_cq[(c, q)]
    r17 = items.get(17)
    if r17:
        v17, vp17 = num(r17.get("값")), num(r17.get("값_적용후"))
        if v17 is not None and vp17 is not None and abs(v17 - vp17) <= 0.5:
            for n in range(29, 36):
                row = items.get(n)
                if row and row.get("값_적용후") in (None, "") and row.get("값") not in (None, ""):
                    blank_2935 += 1
    r19 = items.get(19)
    if r19:
        v19, vp19 = num(r19.get("값")), num(r19.get("값_적용후"))
        if v19 is not None and vp19 is not None and abs(v19 - vp19) <= 0.5:
            for n in range(36, 41):
                row = items.get(n)
                if row and row.get("값_적용후") in (None, "") and row.get("값") not in (None, ""):
                    blank_3640 += 1

print(f"\nfillable blank cells in items 29-35 (gated on item17 unchanged, 2Q/4Q only): {blank_2935}")
print(f"fillable blank cells in items 36-40 (gated on item19 unchanged, 2Q/4Q only): {blank_3640}")

print("\n--- detail: which pairs/items are blank in 15-23 ---")
for (c, q), n in sorted(blank_per_pair.items()):
    items = by_cq[(c, q)]
    blanks = [str(x) for x in range(15, 24) if items.get(x) and items[x].get("값_적용후") in (None, "") and items[x].get("값") not in (None, "")]
    print(f"  {name_of[c]}({c}) {q}: items {blanks}")
