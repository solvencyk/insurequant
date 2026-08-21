# -*- coding: utf-8 -*-
"""Follow-on to fix_20260821_kr0087_2023q2_main_table.py.

Loading item19(시장위험액=10176, verified correct against raw) turned rule `19_market` from
SKIP (item19 was absent) into RED (item19 present but its 36-40 breakdown incomplete - only
item36 existed). This closes that gap: items 37-40 come from raw
data/disclosure/FY2023_Q2/raw/KR0087_동양생명.pdf, dedicated market-risk-detail pages
(fitz idx19-21 = 1-idx p20-22), 당기(2023.2Q) column, 단위 백만원 -> /100 = 억원:

  (3) 주식위험액 현황 (p20): Ⅲ.합계 당기위험액 = 614,809 백만원 -> 6,148.09억
  (4) 부동산위험액 현황 (p20-21): Ⅲ.합계 부동산위험액 = 138,340 백만원 -> 1,383.40억
  (5) 외환위험액 현황 (p21): 계 외환위험액 = 216,630 백만원 -> 2,166.30억
  (6) 자산집중위험액 현황 (p21): 계 위험액 = 0 -> 0

Verified before writing: sqrt(V' MARKET_M V) over (금리=item36 5695.28 already in master,
주식,부동산,외환,자산집중) = 10,175.93 vs stored item19 = 10,176 (diff 0.07억, i.e. 7백만 -
well inside tolerance). MARKET_M imported from kics_json_rules, not retyped.

값_적용후: left null for all four, matching item36's own existing row in this same
(company,quarter) (also null) - this company's raw has no separate market-leaf 적용후 table,
consistent with the main-table fix's item4-13 scope decision (don't invent unevidenced cells).

Usage:
  ...python scripts/fix_20260821_kr0087_2023q2_market_leaves.py --dry-run
  ...python scripts/fix_20260821_kr0087_2023q2_market_leaves.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "kics_disclosure.json"
CODE, NAME, TICKER, KIND, Q = "KR0087", "동양생명", "082640", "생명보험", "2023.2Q"

NEW = {
    37: ("3-2. 주식위험액", 614809 / 100.0),
    38: ("3-3. 부동산위험액", 138340 / 100.0),
    39: ("3-4. 외환위험액", 216630 / 100.0),
    40: ("3-5. 자산집중위험액", 0.0),
}


def fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.2f}".rstrip("0").rstrip(".")


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    before_row_count = len(data)
    before_combos = {(r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")) for r in data}

    existing = {int(r["항목번호"]) for r in data if r.get("원보험사코드") == CODE and r.get("공시분기") == Q}
    inserts = []
    for it, (label, val) in sorted(NEW.items()):
        if it in existing:
            print(f"SKIP item{it}: already present (unexpected)")
            continue
        inserts.append({
            "원보험사코드": CODE, "원수사명": NAME, "티커": TICKER, "생손보여부": KIND,
            "항목번호": it, "항목명": label, "공시분기": Q,
            "값": fmt(val), "값_적용후": None,
        })
    print("삽입 예정:")
    for row in inserts:
        print(f"  item{row['항목번호']} {row['항목명']:<20} 값={row['값']}")

    if dry:
        print("(dry-run; 파일 안 씀)")
        return 0
    if not inserts:
        return 0

    data.extend(inserts)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {TARGET.name}: +{len(inserts)}행")

    after_row_count = len(data)
    after_combos = {(r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")) for r in data}
    print(f"census: row_count {before_row_count} -> {after_row_count} (delta {after_row_count-before_row_count}, "
          f"expected +{len(inserts)})")
    removed = before_combos - after_combos
    added = after_combos - before_combos
    print(f"combo delta: +{len(added)} / -{len(removed)}")
    if removed:
        print(f"!! UNEXPECTED REMOVED: {removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
