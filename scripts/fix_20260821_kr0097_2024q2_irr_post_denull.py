"""Remove fabricated 값_적용후 on KR0097 하나생명 2024.2Q items 41-46.

Root cause (coordinator finding, 2026-08-21): the source table for items
41-46 (p27 of KR0097_하나생명보험_amended.pdf FY2024_Q2, "② 금리위험액 현황")
has columns 충격전 | 충격후(평균회귀·금리상승·금리하락·금리평탄·금리경사) -- a
SHOCK-SCENARIO dimension, not a 경과조치 적용전/적용후 dimension. There is no
post-transition column for these items anywhere in that table. A prior round
mirrored 값_적용후 = 값 for these 6 cells, which fabricates a column the
source does not have.

Structural check across the whole master: among the 18 FSS elective-transition
appliers (_TRANSITION_APPLIERS), KR0097 2024.2Q is the ONLY (company,quarter)
with a non-null items41-46 값_적용후 -- all other 17 appliers correctly carry
none. Owner's standing rule: non-applier post may mirror pre; an applier with
no post disclosed must stay blank (key absent, matching every other blank
post cell in this file -- not JSON null).

Fix: delete the 값_적용후 key from these 6 rows. Values (값, pre) are
untouched -- those came correctly from the same page.

Cell-by-cell UPSERT; prints before/after census.
"""
from __future__ import annotations
import json
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "kics_disclosure.json"

TARGET_CODE = "KR0097"
TARGET_Q = "2024.2Q"
TARGET_ITEMS = set(range(41, 47))


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")

    touched = []
    for r in rows:
        if (
            r.get("원보험사코드") == TARGET_CODE
            and r.get("공시분기") == TARGET_Q
            and r.get("항목번호") in TARGET_ITEMS
        ):
            before_val = r.get("값")
            before_post = r.get("값_적용후")
            had_key = "값_적용후" in r
            if had_key:
                del r["값_적용후"]
            touched.append({
                "item": r.get("항목번호"),
                "name": r.get("항목명"),
                "값(unchanged)": before_val,
                "값_적용후(before)": before_post,
                "had_key_before": had_key,
                "has_key_after": "값_적용후" in r,
            })

    print(f"rows matched: {len(touched)} (expect 6)")
    for t in sorted(touched, key=lambda x: x["item"]):
        print(t)

    if len(touched) != 6:
        print("ABORT: expected exactly 6 matched rows, got", len(touched))
        sys.exit(1)
    if any(t["has_key_after"] for t in touched):
        print("ABORT: 값_적용후 key still present on some row after delete")
        sys.exit(1)

    JSON_PATH.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"wrote {len(rows)} rows (row_count unchanged, 6 cells de-nulled)")


if __name__ == "__main__":
    main()
