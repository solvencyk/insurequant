#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Census the PRINTED_DASH cells in the disclosure-PL backfill staging, restricted to the
5 merge-target items, and show the promotion evidence each one currently carries."""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
d = json.loads((ROOT / "data/_derived/pl_backfill_disclosure_20260918.json")
               .read_text(encoding="utf-8"))
BF = set(d["backfill_item_numbers"])
cells = d["cells"]

print("cell keys:", sorted({k for c in cells for k in c}))
sample = next(c for c in cells if c.get("items"))
print("\nsample cell:", json.dumps({k: v for k, v in sample.items() if k != "components"},
                                   ensure_ascii=False)[:1200])

rows, st = [], Counter()
for c in cells:
    for k, it in (c.get("items") or {}).items():
        n = int(k)
        st[(it.get("dash_state"), n in BF)] += 1
        if it.get("dash_state") == "PRINTED_DASH" and n in BF:
            rows.append((c.get("원보험사코드"), c.get("원보험사명"), c.get("공시분기"), n, it, c))
print("\ndash_state x in-backfill-scope:", {f"{a}|{b}": n for (a, b), n in st.items()})
print(f"\nPRINTED_DASH within the 5 merge items = {len(rows)}")
for code, name, q, n, it, c in sorted(rows, key=lambda r: (r[0], r[2], r[3])):
    print(f"  {code} {name} {q} item{n} {it.get('항목명')} "
          f"값_억원={it.get('값_억원')} 값={it.get('값')} raw={it.get('raw_value')!r} "
          f"excl={c.get('backfill_excluded')} promo="
          f"{json.dumps(it.get('dash_promotion'), ensure_ascii=False)}")
