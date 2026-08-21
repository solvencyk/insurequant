"""KR0080 에이아이에이생명 2023.2Q items 7/9/11 -- same-table correction
discovered while restoring item4 for this cell (fix_20260821_item4_writepath_
restore.py already corrected item4 33836->33793 from raw). The children sum
(items 5-11) still totalled 33836 (the OLD wrong item4), causing a new
"적용후 항등식 위반" RED (공시후=33793 vs 계산후=33836, diff=-43) once
item4's post-mirror moved but its children's own post-mirrors didn't.

Raw source: data/disclosure/FY2023_Q3/raw/KR0080_에이아이에이생명보험.pdf p9
"직전 분기(23.2Q)" column (same page used to raw-verify item4 for KR0080
2023.3Q earlier in this ticket) -- 1.보통주=15,082 2.자본증권=- 3.이익잉여금=
11,797 4.자본조정=- 5.기타포괄손익누계액=959 6.조정준비금=5,955. Sum =
15082+11797+959+5955 = 33,793, exact match to item4.

Master currently holds item7=12053(should be 11797, +256) item9=1687(should
be 959, +728) item11=5014(should be 5955, -941); net +43 explains the whole
gap. Both 값 and 값_적용후 are wrong identically (같은 값으로 미러돼 있음) --
this company is a non-applier, both columns get the same raw-sourced fix.

Cell-by-cell UPSERT; prints before/after.
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "kics_disclosure.json"

CODE = "KR0080"
QUARTER = "2023.2Q"
FIXES = {7: "11797", 9: "959", 11: "5955"}


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")

    touched = []
    for r in rows:
        if r.get("원보험사코드") != CODE or r.get("공시분기") != QUARTER:
            continue
        item_no = r.get("항목번호")
        if item_no not in FIXES:
            continue
        new_val = FIXES[item_no]
        old_val = r.get("값")
        old_post = r.get("값_적용후")
        if str(old_val) != new_val:
            r["값"] = new_val
        if old_post is not None and str(old_post) != new_val:
            r["값_적용후"] = new_val
        touched.append((item_no, r.get("항목명"), old_val, old_post, new_val))

    print(f"cells touched: {len(touched)} (expect 3)")
    for t in sorted(touched):
        print("  ", t)
    if len(touched) != 3:
        print("ABORT: expected exactly 3 rows")
        sys.exit(1)

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows (row_count unchanged)")


if __name__ == "__main__":
    main()
