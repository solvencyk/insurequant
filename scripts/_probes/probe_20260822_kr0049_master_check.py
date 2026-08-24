# -*- coding: utf-8 -*-
"""Check kics_disclosure.json master for KR0049 (AXA sonhae) - all quarters, items 1/14/47-51."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"


def main() -> int:
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    rows = [r for r in data if r.get("원보험사코드") == "KR0049"]
    print(f"KR0049 total rows in master: {len(rows)}")
    quarters = sorted({r["공시분기"] for r in rows})
    print(f"quarters present: {quarters}")
    print()
    for q in quarters:
        qrows = {int(r["항목번호"]): r for r in rows if r["공시분기"] == q}
        items_present = sorted(qrows.keys())
        print(f"--- {q} --- item count={len(items_present)}  items={items_present}")
        for it in (1, 14, 27, 47, 48, 49, 50, 51):
            r = qrows.get(it)
            if r:
                print(f"    item{it}: 값={r.get('값')!r}  값_적용후={r.get('값_적용후')!r}  항목명={r.get('항목명')!r}")
            else:
                print(f"    item{it}: (missing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
