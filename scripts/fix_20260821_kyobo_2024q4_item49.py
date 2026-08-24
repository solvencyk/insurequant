# -*- coding: utf-8 -*-
"""inbox 20260821T1425Z RED-63 followup -- 교보생명보험(KR0073) 2024.4Q item49
오추출 수정 (1건, 3_tier2_composition RED).

## 근거

교보생명 필링은 fitz 텍스트스트림 순서가 뒤섞이는 것으로 이미 알려진 회사다(결함A와 동일
근본원인 계열). `data/disclosure/FY2024_Q4/raw/KR0073_교보생명보험.pdf` page 42(0-idx)의
`get_text().splitlines()` 순서를 직접 추적한 결과:

  line 96: '기본자본'                       <- 이 occurrence 자체는 미사용(타겟 아님)
  line 97: '해약환급금 부족분 상당액 중'      <- item49 라벨 1행
  line 98: '해약환급금 상당액 초과분'         <- item49 라벨 2행("초과분" 포함, 누적매칭 종료)
  line 99: '8,317,860'                     <- **기본자본의 값**(정상 위치는 line 62)이 라벨
  line 100: '9,426,759'                       바로 뒤에 잘못 이어져 있다(텍스트순서 뒤섞임)
  ...
  line 106: '2,511,916'                    <- item49 의 **진짜** 값(전=후 동일)
  line 107: '2,511,916'

즉 라벨 매칭 자체는 정확했으나, 뒤섞인 순서 때문에 라벨 직후에 무관한 기본자본 값이
와서 그걸 그대로 집어 먹었다(기존 로직은 "라벨 다음 숫자 2개"를 잡는데, 이 필링에서는
그 2개가 엉뚱한 행의 값이었다).

`page.get_text("words")` 좌표(y=239.1, x=337/466)로 재확인: item49 = 2,511,916 / 2,511,916
(백만원, 두 컬럼 동일값) -- ÷100 = 25,119.16 / 25,119.16.

**검산(양쪽 컬럼 모두 소수점까지 정확히 재현)**:
  CAPPED 전: min(item47전=31,566.95, item48전=42,601.06) + item49전(25,119.16)
             = 31,566.95 + 25,119.16 = 56,686.11 ≈ 마스터 item3_값(56,686)  (diff 0.11)
  CAPPED 후: min(item47후=20,477.96, item48후=42,601.06) + item49후(25,119.16)
             = 20,477.96 + 25,119.16 = 45,597.12 == 마스터 item3_값_적용후(45,597.12) (정확히 일치)

수정 전(오추출값 83,178.6/94,267.59)으로는 diff -58,059.55(RED) 였던 것이 수정 후 두 컬럼
모두 0.11 이내로 닫힌다 -- 우연이라 보기 어려운 정밀 일치라 이 값이 맞다고 확정한다.

Usage:
  ...python scripts/fix_20260821_kyobo_2024q4_item49.py --dry-run
  ...python scripts/fix_20260821_kyobo_2024q4_item49.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"

CODE, QUARTER, ITEM = "KR0073", "2024.4Q", 49
OLD_PRE, OLD_POST = "83178.6", "94267.59"
NEW_PRE = NEW_POST = "25119.16"


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))

    hits = [r for r in data if r["원보험사코드"] == CODE and r["공시분기"] == QUARTER
            and int(r["항목번호"]) == ITEM]
    if len(hits) != 1:
        print(f"기대 1건, 실제 {len(hits)}건 -- 중단 (수동 확인 필요)")
        return 1
    row = hits[0]
    print(f"수정 전: 값={row.get('값')!r} 값_적용후={row.get('값_적용후')!r}")
    if row.get("값") != OLD_PRE or row.get("값_적용후") != OLD_POST:
        print(f"경고: 예상 기존값({OLD_PRE}/{OLD_POST})과 다르다 -- 이미 수정됐거나"
              " 다른 변경이 있었을 수 있음. 중단.")
        return 1

    if dry:
        print(f"(dry-run) 값 -> {NEW_PRE}, 값_적용후 -> {NEW_POST}")
        return 0

    row["값"] = NEW_PRE
    row["값_적용후"] = NEW_POST
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"수정 완료: 값={NEW_PRE} 값_적용후={NEW_POST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
