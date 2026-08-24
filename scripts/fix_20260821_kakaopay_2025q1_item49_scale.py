# -*- coding: utf-8 -*-
"""inbox 20260821T1425Z RED-63 followup -- 카카오페이손해보험(KR1098) 2025.1Q item49
스케일 버그 수정 (1건).

## 근거

`fix_20260821_tier2_limit_lines.py`의 스케일 게이트가 "item48(보완자본 한도) ≈ 0 이면
스케일 무관하게 통과"라는 단축을 썼는데, 이 회사·분기는 item48=0 이지만 item49(해약환급금
부족분 상당액 중 초과분)=1,553(raw, 백만원)으로 **실질값**이었다. 단축이 47/48/49 전체에
일괄 적용돼 item49 가 스케일 판정 없이(=1.0 가정) 그대로 실렸다.

raw (`data/disclosure/FY2025_Q1/raw/KR1098_카카오페이손해보험.pdf`, "[지급여력비율의
경과조치 적용에 관한 사항] (1) 공통적용 경과조치 관련" 표): item49 = 1,553 / 1,553 (백만원),
표 자신의 종결행 "지급여력기준금액"(anchor) = 14,863 / 14,863 (백만원).

마스터 item14_적용전(SCR) = 149(억원). anchor(14,863) / item14_pre(149) = 99.75 ≈ 100
→ **스케일 0.01(÷100) 이 맞다** — item47/48(둘 다 0, 스케일 무관)이 아니라 item49 기준으로
재판정해야 했다. 검산: 보완자본(item3, 마스터 기존값)=16. CAPPED 식
`min(47,48)+49 = min(0,0)+15.53 = 15.53 ≈ 16`(diff 0.47, 반올림오차 이내) — 수정 후 정확히
재현된다(수정 전은 1553 대 16, diff 1537).

스크립트(`fix_20260821_tier2_limit_lines.py`)의 스케일 게이트 자체는 이 세션에서 이미
고쳤다(item47/49 도 함께 사실상 0 일 때만 단축을 쓰도록, `_trivial()` 가드 추가) — 신규
적재분은 앞으로 이 버그 없이 나온다. 이 스크립트는 **이미 잘못 적재된 기존 셀 1개**를
UPSERT(idempotent 재실행 가능)로 고친다.

Usage:
  ...python scripts/fix_20260821_kakaopay_2025q1_item49_scale.py --dry-run
  ...python scripts/fix_20260821_kakaopay_2025q1_item49_scale.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"

CODE, QUARTER, ITEM = "KR1098", "2025.1Q", 49
OLD_VALUE = "1553"
NEW_VALUE = "15.53"


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
    if row.get("값") != OLD_VALUE or row.get("값_적용후") != OLD_VALUE:
        print(f"경고: 예상 기존값({OLD_VALUE}/{OLD_VALUE})과 다르다 -- 이미 수정됐거나"
              " 다른 변경이 있었을 수 있음. 중단.")
        return 1

    if dry:
        print(f"(dry-run) 값/값_적용후 -> {NEW_VALUE}")
        return 0

    row["값"] = NEW_VALUE
    row["값_적용후"] = NEW_VALUE
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"수정 완료: 값=값_적용후={NEW_VALUE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
