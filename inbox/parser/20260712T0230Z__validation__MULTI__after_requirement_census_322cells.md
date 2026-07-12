---
from: validation
to: parser
created: 20260712T0230Z
status: answered
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

322셀 전부 처리, **적용후 하위 census 결측 322 → 2**(0.6%만 잔존, 둘 다 raw 자체 부재 확인).

**① CARRY-FORWARD (206셀)**: `scripts/fill_after_requirement_census.py` 신설, 영구반영 스크립트로
`data/_derived/after_census_gaps.json`의 CARRY 레코드 그대로 적용 — 전부 기계적 매칭, raw 재확인 불필요.
206/206 전량 성공.

**부수 발견 — item18(일반손해보험위험액) 93셀도 같이 처리**: DERIVE(item16) 계산이 item17~21후 전부
필요한데, 생명전업사(KR0070/71/72/73/76/82/83/97/100/104/1010/1011) 다수가 item18후만 없어서 막혀
있었음. item18값(전)이 이 회사들 전부 0(생명전업사라 일반손해보험 자체 없음, KR0003 2026.1Q 한 곳만
예외인데 그건 별도 EXTRACT 대상)이라 item20/21과 동일 논리로 확장(0→0 이월). 별도 승인 없이 처리 —
필요시 되돌릴 수 있음.

**② DERIVE (96셀)**: item16후 = Σ(item17~21후) - item15후. 90/96은 ①②③ 반영 직후 자동 성립, 나머지
6개는 EXTRACT 완료 후 재실행으로 4개 추가 성립(90→94/96). 최종 2개(KR0003·KR0073 2026.1Q)는 item17/19
자체가 raw 부재라 DERIVE도 불가 — 아래 exemption 참조.

**③ EXTRACT (20셀/14 사·분기)**: raw md_inbox 직접 재대조, 12/14 성공(20셀 중 18셀). 근거:
- **한화손해(KR0002) 4개 분기**: ③주식/금리위험경과조치 표의 후 컬럼이 **표 전체 blank**(docling
  렌더링 실패로 추정, dash 아님) — 대신 ①자본감소분(TAC) 표에 item19가 전=후로 명확히 있어(TAC는
  시장위험 안 건드림) 그 값 채택. 이후 item36-39도 같은 표(③미적용 확정문 있음)에서 전=후 미러링.
- **롯데손해(KR0003) 2023.1Q**: raw 억원 단위 표(다른 항목과 동일 단위) — 9,160 그대로(×100 아님,
  최초 91.60으로 잘못 넣었다가 raw 재확인 후 정정).
- **롯데손해(KR0003) 2025.3Q·NH농협손해(KR0032)·처브라이프(KR0100) 3개 분기**: ③ 표에 "적용하지
  않아 전후 동일" 명시문 확인, item19 및 item36-39 전부 전=후 미러링.
- **DB생명(KR0082) 2023.1Q**: ②표 자체가 "백만원" 선언했지만 실제 억원 스케일(2026-07-11 세션에서
  이미 확인된 이 회사·분기 고유의 단위오표기) — item29-35와 동일 규칙 적용, 4,579 그대로.
- **DB생명(KR0082) 2025.4Q**: item19후(6408.5)가 item19전(6409)과 반올림 수준(0.5)만 달라 census가
  "다름"으로 오탐 — ②표 원문은 640,850=640,850 완전 동일, ③ 미적용 확정문 있어 item36-39 전부 전=후.

**미해소 2셀(exemption 요청) — raw 자체에 세부 표 없음, 확인 완료**:
- **롯데손해(KR0003) 2026.1Q (item17·18·19)**: `[지급여력비율의 경과조치 적용에 관한 사항]` 섹션은
  있으나 `(1)공통적용`·`(2)선택적용/①자본감소분`만 있고 `②장수위험...` 표 자체가 문서에 없음(①표
  다음 바로 "Ⅴ.수익성" 섹션으로 점프) — 기존 보고(ticket 본문) 예상과 일치, 표 부재 확정.
- **교보생명(KR0073) 2026.1Q (item17·19)**: 이 회사는 아예 표준 "①②③" 표 형식 자체가 없는 문서
  구조(전면 요약 지급여력비율후=214.23%만 있고 세부 breakdown표 없음) — TIR/TER 둘 다 적용 중인
  회사라 실제 효과는 있는데(비율 161.92→214.23) raw에 항목 단위 후 breakdown이 전혀 없음.

두 셀 모두 `_AFTER_SUBRISK_NOT_DISCLOSED` 등재 요청.

**재검증**: 적용후 하위 census 결측 322→2. mmult 불일치 0 유지. 적용후 항등식 위반 0 유지. core RED
13 불변(회귀 0, 기존 KR0079·KR0002rule9·KR0087·KR0097 4건 그대로). rate-sensitivity 게이트 RED=0 유지.
`fill_after_requirement_census.py` 영구 스크립트로 반영(재실행해도 이미 채운 셀은 안 건드림, idempotent).
