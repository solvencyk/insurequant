"""KR0087 동양생명 2023.2Q items 36-39 값_적용후 -- census RED from inbox
20260821T1505Z item 2 (item19후 present, 36-39후 missing).

Verified from raw (data/disclosure/FY2023_Q2/raw/KR0087_동양생명.pdf), NOT
assumed:
  - p11 신청현황(application status) table: TFI=O(공통), 보고기한연장=O
    (공통), TAC=X, TIR=X, TER=X, TIRR=X -- ALL FOUR elective transitions
    not applied (TER covers 주식위험, TIRR covers 금리위험 -- both the
    market-risk-relevant ones are explicitly X here, not inferred).
  - p12-13 narrative: "(다) 주식위험 경과조치 또는 금리위험 경과조치:
    주식위험 경과조치를 미적용으로 경과조치 전·후 금액 및 비율이 동일"
    AND the broader "주) 지급여력비율 경과조치 미적용으로 경과조치 전·후
    금액 및 비율이 동일" (this blanket note covers the whole ratio chain,
    which requires item14/Ⅰ.기본요구자본/시장위험액 to be unchanged too --
    a component-level change would break the stated "전체 동일").
  - p12 공통(TFI) 표: 지급여력기준금액 2,738,518 (전) = 2,738,518 (후),
    identical -- TFI only reclassifies capital tier (기본/보완자본), never
    touches the requirement side, consistent with every other company seen
    this session.
  - item19(시장위험액, parent) already carries 값_적용후=값 (10176=10176)
    in the live master -- only children 36-39 were missing the mirror.

item40(자산집중위험액)=0 already has no 후 gap (0 either way); 41-46 (IRR
scenario) not touched here -- separate concept, out of scope.

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

CODE = "KR0087"
QUARTER = "2023.2Q"
TARGET_ITEMS = {36, 37, 38, 39}


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")

    touched = []
    for r in rows:
        if (
            r.get("원보험사코드") == CODE
            and r.get("공시분기") == QUARTER
            and r.get("항목번호") in TARGET_ITEMS
        ):
            pre = r.get("값")
            post_before = r.get("값_적용후")
            if post_before is not None:
                print(f"  SKIP item{r.get('항목번호')}: 값_적용후 already set ({post_before})")
                continue
            r["값_적용후"] = pre
            touched.append((r.get("항목번호"), r.get("항목명"), pre))

    print(f"\ncells set (값_적용후 = 값, non-applier mirror): {len(touched)} (expect 4)")
    for t in sorted(touched):
        print("  ", t)

    if len(touched) != 4:
        print("ABORT: expected exactly 4 cells")
        sys.exit(1)

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {len(rows)} rows (row_count unchanged) -- {len(touched)} cells touched")


if __name__ == "__main__":
    main()
