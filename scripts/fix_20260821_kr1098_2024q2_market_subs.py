"""KR1098 카카오페이손해 2024.2Q items 36-40 (시장위험 하위) -- fixes the
rule 19_market RED my own census load (fix_20260821_kr1098_2024q2q3_load.py)
introduced by leaving these blank (item19=8 present with no children is a
missing-input RED, not SKIP).

Source: data/disclosure/FY2024_Q2/raw/KR1098_카카오페이손해보험_amended2.pdf
(scanned, no text layer -- read via get_pixmap(dpi=100) + vision, same as
the rest of this ticket's KR1098 work), 당기(24.2Q) column:
  - p26/27 "① 금리위험액 현황": Ⅳ.금리위험액 = 24 백만원 -> item36 = 0.24
  - p29 "③ 주식위험액 현황": "해당사항 없음" -> item37 = 0
  - p29 "④ 부동산위험액 현황": Ⅲ.합계 = "-" (all dashes) -> item38 = 0
  - p29 "⑤ 외환위험액 현황": "해당사항 없음" -> item39 = 0
  - p29 "⑥ 자산집중위험액 현황": 계 = 770 백만원 -> item40 = 7.70

Cross-check: diversified = sqrt(0.24^2 + 7.70^2 + 2*0.25*0.24*7.70) = 7.76,
rounds to 8 -- matches the disclosed item19 (already loaded) exactly.
Non-applier (confirmed earlier in this ticket) -> 값_적용후 mirrors 값.

Cell-by-cell UPSERT (new rows, item19 parent already exists so this is
INSERT not overwrite). Prints before/after.
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "kics_disclosure.json"

CODE = "KR1098"
NAME = "카카오페이손해보험"
TICKER = "X"
KIND = "손해보험"
QUARTER = "2024.2Q"

ITEMS = [
    (36, "3-1. 금리위험액", "0.24"),
    (37, "3-2. 주식위험액", "0"),
    (38, "3-3. 부동산위험액", "0"),
    (39, "3-4. 외환위험액", "0"),
    (40, "3-5. 자산집중위험액", "7.70"),
]


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")

    existing = [
        r for r in rows
        if r.get("원보험사코드") == CODE and r.get("공시분기") == QUARTER
        and r.get("항목번호") in {n for n, *_ in ITEMS}
    ]
    if existing:
        print(f"ABORT: {len(existing)} of these rows already exist")
        sys.exit(1)

    new_rows = []
    for item_no, item_name, val in ITEMS:
        new_rows.append({
            "원보험사코드": CODE,
            "원수사명": NAME,
            "티커": TICKER,
            "생손보여부": KIND,
            "항목번호": item_no,
            "항목명": item_name,
            "공시분기": QUARTER,
            "값": val,
            "값_적용후": val,
        })

    print(f"inserting {len(new_rows)} rows")
    for r in new_rows:
        print("  ", r["항목번호"], r["항목명"], r["값"])
    rows.extend(new_rows)

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows (was {len(rows) - len(new_rows)}, +{len(new_rows)})")


if __name__ == "__main__":
    main()
