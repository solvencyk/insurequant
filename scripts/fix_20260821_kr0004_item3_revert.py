"""Revert/correct KR0004 예별손해 2024.2Q item3 -- my own
fix_20260821_item3_writepath_restore.py picked a WORSE value for this one
cell out of the 80 it touched, and it's the direct cause of the new "rule 1"
RED (item1=item2+item3, diff=-2.98) surfaced after that run.

What happened: my restoration script's raw-match landed on the coarse
integer "[경과조치 적용 전 지급여력비율 세부]" comparative table
(md_inbox/FY2024_Q2/KR0004_예별손해보험.md L268-270: 지급여력금액=3,572
기본자본=498 보완자본=3,085) and used 3,085. But that table is internally
inconsistent for this exact column (498+3085=3583, not 3572) -- a
source-side rounding/typo, same class of issue as the KR0003 2023.4Q cell
already excluded in that script's docstring, just not caught because THIS
company/quarter had children_present_count=7 (all present, incl. item10)
so it slipped through the "no unclassified" pass.

The authoritative source is a SEPARATE, more precise table two sections
later on the same page (L300-313, "(1) 공통적용 경과조치 관련", 백만원
units): 지급여력금액=357,193 기본자본=48,998 보완자본=308,195 (both
경과조치 적용전/후 columns identical for 보완자본, i.e. TFI doesn't move
it here). /100 -> 3571.93 / 489.98 / 3081.95 -- this is EXACTLY what item2
(값=값_적용후=489.98) and item1 (3572, both columns) and item3's OWN
값_적용후 (3081.95, untouched by my restore script, already correct from a
prior session) already hold. Setting item3's 값 to match 값_적용후 restores
internal consistency: 489.98+3081.95=3571.93, rounds to 3572 = item1.

Single-cell UPSERT.
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "kics_disclosure.json"


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")

    hit = None
    for r in rows:
        if (r.get("원보험사코드") == "KR0004" and r.get("공시분기") == "2024.2Q"
                and r.get("항목번호") == 3):
            hit = r
            break
    if hit is None:
        print("ABORT: row not found")
        sys.exit(1)

    old = hit.get("값")
    if str(old) != "3085":
        print(f"ABORT: 값 is {old!r}, expected '3085' (state drifted)")
        sys.exit(1)

    hit["값"] = "3081.95"
    print(f"item3 값: {old!r} -> '3081.95' (matches existing 값_적용후={hit.get('값_적용후')!r})")

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows (row_count unchanged)")


if __name__ == "__main__":
    main()
