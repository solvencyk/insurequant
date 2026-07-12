---
from: validation
to: parser
created: 20260712T0230Z
route: reparse
company: MULTI (18 선택경과조치 적용사)
period: 2023.1Q~2026.1Q
lane: kics
priority: HIGH
---

## 적용후 요구자본·시장하위 census 322셀 결측 — 적용전과 동일검증 배선 후 적발

owner 재지시(2026-07-12): "적용후 숫자도 적용전 검증로직과 **완전히 동일**하게 — mmult·생명장기/시장 각
하위위험 mmult·census 전부 적용." 기존 적용후 게이트는 mmult(item17/19 leaf 닫힘)만 봤고 **요구자본
구성요소(15→16~21) census가 없었음** + 적용후 항등식(R6 등)은 결측셀을 skip → 요구자본 부분충전이
census/identity 양쪽으로 샜음.

**신설**: `_parent_present_child_incomplete_after` (적용전 `_parent_present_child_incomplete` 미러).
부모후 present인데 '적용전이 present&material'인 자식후 결측 = RED(blocking). 부모맵:
`{15:(16~21), 17:(29~35), 19:(36~40)}`. 결과 **149 (부모,분기) = 322 항목셀**.

전량 목록·판정 근거: `data/_derived/after_census_gaps.json` (fix_class·detail 포함).

### fix-class별 (parser 작업)

**① DERIVE — 96셀 (분산효과 item16후).** 파생값: `item16후 = Σ(item17~21후) - item15후`
(후완비 케이스 119/119 성립 검증). item27/28후 산출(recalc_basic_capital_ratio_post.py)과 동일 방식.
**주의: 17~21후가 다 채워진 뒤 마지막에 산출** (아래 ②③ 먼저).

**② CARRY-FORWARD — 206셀 (경과조치 무관 → 후=전).** raw 재파싱 불필요, 적용전값 복사:
- 신용위험(item20)후=전, 운영위험(item21)후=전 (검증: 신용 후=전 217/218·운영 213/213).
- 시장 하위위험(item36~40)후=전 **단 item19후=item19전인 분기만** (시장 경과조치 무효과 → 하위 불변).
  json의 detail에 `item19후=전` 명시된 셀들.

**③ EXTRACT — 20셀 / 14 (회사,분기): raw 재추출 (핵심작업).** 경과조치로 실제 변동 → 값 도출 필요:

| 회사 | 분기 | 결측 항목후 |
|---|---|---|
| 한화손해(KR0002) | 2024.2Q·2025.1Q·2025.3Q·2026.1Q | item19(시장) |
| 롯데손해(KR0003) | 2023.1Q·2025.3Q | item19 |
| 롯데손해(KR0003) | 2026.1Q | item17·18·19 (기존 보고: raw tier-split 표 부재 → 확인 후 부재면 exemption 회신) |
| NH농협손해(KR0032) | 2024.4Q | item19 |
| 교보생명(KR0073) | 2026.1Q | item17·19 |
| DB생명(KR0082) | 2023.1Q | item19 |
| DB생명(KR0082) | 2025.4Q | item36·37·38·39 (시장 하위위험, item19후≠전) |
| 처브(KR0100) | 2023.1Q·2024.4Q·2025.4Q | item19 |

**raw에 값이 실재하면 추출, raw부재(표 없음)면 그 셀만 documented exemption 사유 회신** (validation이
`_AFTER_SUBRISK_NOT_DISCLOSED`에 등재). "parsing 불가"는 raw부재 확인분만 인정 — 그 외는 전부 채울 것.

### 제외 (이미 documented exemption, 재작업 대상 아님)
`_AFTER_SUBRISK_NOT_DISCLOSED`: 하나생명 24.4Q/26.1Q·농협생명 23.1Q·처브 24.3Q·흥국화재 24.4Q.

### 완료 기준
- ①②③ 반영 후 `python scripts/validate_kics_disclosure.py` → **"적용후 하위 census 결측: 0"**
  (+ mmult 불일치 0 유지, 적용후 항등식 0 유지).
- kics_disclosure.json + templates/kics_disclosure.json 동기화.
- fill 스크립트(예: fill_post_transition_to_disclosure.py)에 영구반영(재실행에도 유지).

## 답변 (parser 작성 — 처리 후)

<!-- 처리 결과·EXTRACT 중 raw부재 회신분·잔여 exemption 후보 기입 -->
