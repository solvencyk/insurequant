"""KR1098 카카오페이손해 2024.2Q items 41-46 (금리위험 순자산가치 시나리오)
-- fixes rule 36_irr RED (item36 present, no 41-46 to derive-check against).

Source: data/disclosure/FY2024_Q2/raw/KR1098_카카오페이손해보험_amended2.pdf
p26/27 "② 금리위험액 현황", 당기(24.2Q) column (단위: 백만원):
  Ⅲ. 순자산가치  충격전=(3,522) 평균회귀=(3,529) 금리상승=(3,506)
                  금리하락=(3,538) 금리평탄=(3,515) 금리경사=(3,529)
  (parens = negative per Korean disclosure convention)

Cross-check via the repo's own derive formula (kics-market-risk-decomposition
§7-7): R_x = item41 - item(43..46), R평균회귀 = item41-item42 (signed).
  R평균회귀 = -3522-(-3529) = 7
  R상승      = -3522-(-3506) = -16
  R하락      = -3522-(-3538) = 16
  R평탄      = -3522-(-3515) = -7
  R경사      = -3522-(-3529) = 7
  item36 = sqrt(max(16,16)^2 + max(7,7)^2) + 7 = sqrt(256+49)+7 = 24.46
  -> rounds to 24 백만원 = 0.24억원, EXACTLY matching item36 already loaded
     in fix_20260821_kr1098_2024q2_market_subs.py. Not a coincidence --
     confirms this is the right table and the right column.

No 경과조치 적용전/적용후 dimension exists for these items anywhere (this is
a shock-scenario axis, not a transition axis -- same structural fact the
coordinator's KR0097 correction established earlier in this ticket) -- no
값_적용후 written, matching every other company's items 41-46.

Cell-by-cell INSERT (new rows). Prints before/after.
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

# 백만원 -> 억원 (/100), sign per Korean paren-negative convention
ITEMS = [
    (41, "3-1-0. 금리위험 순자산가치(충격전)", "-35.22"),
    (42, "3-1-1. 금리위험 순자산가치(평균회귀)", "-35.29"),
    (43, "3-1-2. 금리위험 순자산가치(금리상승)", "-35.06"),
    (44, "3-1-3. 금리위험 순자산가치(금리하락)", "-35.38"),
    (45, "3-1-4. 금리위험 순자산가치(금리평탄)", "-35.15"),
    (46, "3-1-5. 금리위험 순자산가치(금리경사)", "-35.29"),
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
            # no 값_적용후 -- no post-transition dimension exists for this axis
        })

    print(f"inserting {len(new_rows)} rows")
    for r in new_rows:
        print("  ", r["항목번호"], r["항목명"], r["값"])
    rows.extend(new_rows)

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows (was {len(rows) - len(new_rows)}, +{len(new_rows)})")


if __name__ == "__main__":
    main()
