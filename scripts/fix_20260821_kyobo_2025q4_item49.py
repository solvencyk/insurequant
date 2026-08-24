# -*- coding: utf-8 -*-
"""inbox 20260821T1425Z RED-63 followup -- 교보생명보험(KR0073) 2025.4Q item49 결측
INSERT (1건, 47_tier2_census / _post RED: TIER2_PARTIAL_ROWS [47,48] 는 있는데 [49] 결측).

## 근거

같은 회사의 텍스트순서 뒤섞임 문제(2024.4Q 와 동일 계열)로 라벨 매칭이 실패해 item49 가
아예 안 실렸다. `page.get_text("words")` 좌표로 직접 확인
(`data/disclosure/FY2025_Q4/raw/KR0073_교보생명보험.pdf`, 0-idx page 51):

  y=233.9: "해약환급금 부족분 상당액 중"
  y=239.0: 3,569,776@x=334 | 3,569,776@x=456     <- item49 값(전=후 동일)
  y=244.3: "해약환급금 상당액 초과분"

백만원 -> ÷100 = 35,697.76 / 35,697.76.

**검산(양쪽 컬럼 모두 소수점까지 정확히 재현)**:
  CAPPED 전: min(item47전=35,874.10, item48전=42,912.44) + item49전(35,697.76)
             = 35,874.10 + 35,697.76 = 71,571.86 ≈ 마스터 item3_값(71,572)      (diff 0.14)
  CAPPED 후: min(item47후=24,785.11, item48후=42,912.44) + item49후(35,697.76)
             = 24,785.11 + 35,697.76 = 60,482.87 == 마스터 item3_값_적용후(60,482.87) (정확히 일치)

Usage:
  ...python scripts/fix_20260821_kyobo_2025q4_item49.py --dry-run
  ...python scripts/fix_20260821_kyobo_2025q4_item49.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"

CODE, QUARTER, ITEM = "KR0073", "2025.4Q", 49
VALUE = "35697.76"
LABEL = "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분"


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))

    existing = [r for r in data if r["원보험사코드"] == CODE and r["공시분기"] == QUARTER
                and int(r["항목번호"]) == ITEM]
    if existing:
        print(f"이미 존재함 (값={existing[0].get('값')!r}) -- 중단, INSERT 스크립트는 신규용")
        return 1

    # 같은 (회사,분기)의 다른 항목에서 원수사명/티커/생손보여부를 그대로 가져온다
    sibling = next((r for r in data if r["원보험사코드"] == CODE and r["공시분기"] == QUARTER), None)
    if sibling is None:
        print("형제 행을 못 찾음 -- 중단")
        return 1

    row = {
        "원보험사코드": CODE,
        "원수사명": sibling.get("원수사명"),
        "티커": sibling.get("티커"),
        "생손보여부": sibling.get("생손보여부"),
        "항목번호": ITEM,
        "항목명": LABEL,
        "공시분기": QUARTER,
        "값": VALUE,
        "값_적용후": VALUE,
    }
    print(f"INSERT: {row}")
    if dry:
        print("(dry-run; 파일 안 씀)")
        return 0

    data.append(row)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"1행 INSERT 완료 (row_count -> {len(data):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
