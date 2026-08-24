# -*- coding: utf-8 -*-
"""inbox 20260821T1425Z RED-63 followup -- 신한이지손해보험(KR0051) 2023.1Q~2023.3Q
item47/49 저신뢰 적재분 되돌리기 (4행 DELETE).

## 경위

이번 세션에서 스케일 게이트에 SCR_ANCHOR_FALLBACK 축을 추가했다(카카오페이 2025.1Q item49
스케일버그 수정 목적, RED-63 소관). 이 축이 **부수효과로** 신한이지의 기존 "스케일불명"
3개 분기(2023.1Q~2023.3Q, 비차단 SKIP 상태였음)의 스케일도 함께 풀어 47/48/49 일부를
신규 INSERT 했다(4행). 재검증(`validate_kics_disclosure.py`)을 돌려보니 이 3개 분기가
`47_tier2_census`(+`_post`) **TIER2_PARTIAL_ROWS RED 6건**을 새로 발생시켰다 — 이전엔
없던 신규 blocking RED 다(RED-63 은 이 회사를 포함하지 않았다).

## 왜 되돌리나 (근거)

원문(`data/disclosure/FY2023_Q1/raw/KR0051_신한이지손해보험.pdf` page 8)을 직접 확인한
결과, 이 회사의 [지급여력비율의 경과조치 적용에 관한 사항] 표는 **라벨과 값이 완전히
분리된 블록**으로 인쇄돼 있다(먼저 값 몇 개가 라벨 없이 나열되고, 그 다음 라벨들이
쭉 나열되고, 그 다음 다시 값들이 나열되는 순서 — 정상적인 "라벨\n값\n값" 반복 구조가
아니다). 이건 기존 결함C 조사에서 확인한 3가지 줄바꿈 변형이나 이번 세션에서 고친
4번째 변형(단어단위 분할)과도 다른, **완전히 다른 레이아웃**이다.

이런 구조에서는 "라벨 다음 숫자 2개를 잡는다"는 기존 로직이 **어느 라벨 뒤에 어느 숫자가
따라오는지 신뢰할 근거가 없다** — SCR_ANCHOR_FALLBACK 이 스케일(배율) 자체는 올바르게
판정했더라도(anchor/item14 비율이 실제로 1 or 100 에 가까웠다), **그 배율을 적용할 값
자체가 엉뚱한 행에서 온 것일 수 있다.** 실제로 item47=503(2023.1Q)이 raw 어느 행의
값인지 눈으로 재구성하려면 좌표 기반 재작업이 필요한데, 이건 RED-63 소관 밖의 별도
회사이고 이 세션에서 그 정밀 작업을 하지 않았다.

**"틀린 값을 싣느니 빈 칸"** — 스케일은 맞았을 수 있어도 값 자체의 행 귀속을 확신할 수
없으므로, 이번 세션이 만든 저신뢰 4행만 되돌린다. 결과적으로 이 3개 분기는 되돌리기
전 상태(스케일불명/미검출, 비차단 SKIP)로 복귀한다. `fix_20260821_tier2_limit_lines.py`
의 SCR_ANCHOR_FALLBACK 로직 자체는 유지한다(카카오페이 2025.1Q 등 정상 레이아웃 회사에는
올바르게 작동하며, 신한이지처럼 라벨/값이 완전분리된 레이아웃에서만 이런 문제가 생긴다 —
그 경우조차 "적재 안 함"이 아니라 "적재는 하되 신뢰 못 함"이라는 게 이번에 새로 발견한
함정이라 별도 후속조사가 필요하다).

Usage:
  ...python scripts/fix_20260821_revert_sinhanez_low_confidence.py --dry-run
  ...python scripts/fix_20260821_revert_sinhanez_low_confidence.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"

TARGETS = {
    ("KR0051", "2023.1Q", 47),
    ("KR0051", "2023.2Q", 47),
    ("KR0051", "2023.3Q", 47),
    ("KR0051", "2023.3Q", 49),
}


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))

    keep = []
    removed = []
    for r in data:
        key = (r["원보험사코드"], r["공시분기"], int(r["항목번호"]))
        if key in TARGETS:
            removed.append(r)
        else:
            keep.append(r)

    print(f"제거 대상 {len(removed)}행 (기대 {len(TARGETS)}행):")
    for r in removed:
        print(f"  {r}")

    if len(removed) != len(TARGETS):
        print("경고: 기대 건수와 다르다 -- 중단 (수동 확인 필요)")
        return 1

    if dry:
        print("(dry-run; 파일 안 씀)")
        return 0

    TARGET.write_text(json.dumps(keep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(removed)}행 DELETE, wrote {TARGET.name}  (row_count {len(data):,} -> {len(keep):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
