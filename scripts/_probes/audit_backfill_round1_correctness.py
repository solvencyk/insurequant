"""Round 1 ran backfill_post_transition_when_not_applied.py, which mirrored
items 4-13/16-26/29-46 for 14 (name,quarter) pairs classified "safe" by its
OLD item1/14/27-only (tol 0.01) check. We've since learned item28 (and by
extension item2/3/12/13, the capital-TIER split) can shift a lot via TFI
even when item1/14/27 look flat. Check whether any of those 14 pairs
actually have a real item28 divergence -- if so, items 12/13 (and 2/3, if
also touched) may have been WRONGLY mirrored with stale 전 values."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent.parent
data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))

TOUCHED_PAIRS = [
    ("KB라이프생명", "2024.2Q"),
    ("동양생명", "2024.1Q"),
    ("동양생명", "2025.4Q"),
    ("비엔피파리바카디프생명보험", "2023.1Q"),
    ("비엔피파리바카디프생명보험", "2023.3Q"),
    ("비엔피파리바카디프생명보험", "2024.1Q"),
    ("비엔피파리바카디프생명보험", "2024.3Q"),
    ("비엔피파리바카디프생명보험", "2025.1Q"),
    ("비엔피파리바카디프생명보험", "2025.2Q"),
    ("신한이지손해보험", "2024.1Q"),
    ("신한이지손해보험", "2024.3Q"),
    ("신한이지손해보험", "2025.1Q"),
    ("카카오페이손해보험", "2023.1Q"),
    ("카카오페이손해보험", "2023.2Q"),
]


def num(v):
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


by_cq: dict[tuple[str, str], dict[int, dict]] = {}
for r in data:
    by_cq.setdefault((r["원수사명"], r["공시분기"]), {})[r["항목번호"]] = r

for name, q in TOUCHED_PAIRS:
    items = by_cq.get((name, q), {})
    r1, r2, r3, r12, r13, r14, r27, r28 = (items.get(n) for n in (1, 2, 3, 12, 13, 14, 27, 28))
    print(f"=== {name} {q} ===")
    for label, row in [("item1", r1), ("item2", r2), ("item3", r3), ("item12", r12),
                        ("item13", r13), ("item14", r14), ("item27", r27), ("item28", r28)]:
        if row is None:
            print(f"  {label}: <no row>")
            continue
        v, vp = num(row.get("값")), num(row.get("값_적용후"))
        d = abs(v - vp) if (v is not None and vp is not None) else None
        print(f"  {label}: 값={row.get('값')} 값_적용후={row.get('값_적용후')} |diff|={d}")
