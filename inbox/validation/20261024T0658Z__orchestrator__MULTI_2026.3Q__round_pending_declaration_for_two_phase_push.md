---
from: orchestrator
to: validation
created: 20261024T0658Z
status: open
route: backlog
company: MULTI
period: 2026.3Q
iter: 1
---

## 미결 (sender 작성)

owner 결정(2026-10-24): 2026.3Q 는 **DART 묶음을 먼저 푸시하고, 경영공시 묶음을 그다음에 푸시한다**(KIDI 는 늦게 오므로 기다리지 않는다). 계획 `docs/flows/round_2026_3Q_plan.md` §1-1.
이 결정은 「2026.3Q 행은 한 번에 푸시」 전제(같은 문서 §6)와 충돌한다. 분기 지평(`scripts/_quarter_horizon.py`)이 5개 마스터(`PL_breakdown`·`CSM_waterfall`·`IFRS17_BS`·`kics_disclosure`·`dividend`)의 최댓값에서 파생되므로, 1차 푸시에서 PL·CSM·BS·dividend 가 2026.3Q 를 담는 순간 지평이 2026.3Q 로 늘고 아직 소스가 없는 칸이 전부 hole 로 읽힌다.

1차 푸시에 들어가는 것(DART 소스): PL 24사(전 항목) · CSM 워터폴 23사 · IFRS17_BS 24사 · dividend 24사 + 3Q 보고서 전기 열로 고치는 기존 분기 칸. 2차 푸시(경영공시 소스): K-ICS 전부 · PL·BS 의 경영공시 15사 + 재보사 8곳 · 라이나 CSM · ILP · 자본증권 3종 · xlsx·public_exports.

**1차 푸시 상태에서 예상되는 RED(측정으로 확인해 주세요 — 아래는 코드 판독 추정입니다):**
- `MASTER_HOLE` PL: 경영공시 15사 + 재보사 8곳 중 활성 회사(약 22~23) × 2026.3Q. IFRS17_BS 도 같은 모양, CSM 은 라이나 1사.
- `NB_CENSUS_MISSING` 24건(CSM 에 3Q 가 있고 NB 에 없음; KIDI 202609 대기. 2Q 선례는 건별 baseline YELLOW).
- K-ICS census(`_coverage_census`)는 마스터에 있는 분기만 순회하므로 3Q 행이 0 이면 안 걸릴 것으로 보이나 `check_census`·`validate_master_tables` 의 지평 순회가 어느 쪽인지 확인이 필요합니다.
- 골든(`test_kics_rules_golden` 등)과 입력 지문은 마스터 변경 때문에 갱신이 필요합니다(RED 가 남은 채 `--update` 금지).

## 요청

1. **먼저 측정:** 작업 사본에서 1차 푸시 상태(DART 24사 3Q 행만 있는 마스터)를 모의로 만들어 어떤 게이트가 무엇을 RED 로 내는지 목록을 만들어 주세요. 코드 수정 전에.
2. **설계(새 게이트 룰 설계라 Opus 대상, CLAUDE.md §10):** 2단계 라운드를 위한 「대기 선언」. 요구 조건:
   - 칸 단위로만 선언한다(마스터·회사·분기). 통째 SKIP·분기 전체 면제 금지(census 필수 규칙: SKIP-on-missing 금지).
   - 기존 `_PL_SOURCE_ABSENT`·`_CENSUS_SOURCE_ABSENT` 와 같은 원칙으로 **매 실행 재검산**: 해당 회사의 3Q raw 가 디스크에 아직 없고 매니페스트가 미수집이라고 말할 때만 인정한다. raw 가 이미 있는데 마스터에 없으면 그대로 RED.
   - **만료:** 선언은 2차 푸시에서 비워진다. 만료일이 지나거나 선언이 남은 채 2차 푸시 게이트를 돌리면 RED 가 되게 한다(이 만료를 거는 테스트 포함).
   - 이미 적재된 3Q 칸(DART 24사)은 모든 기존 게이트를 그대로 받는다. 선언은 「없는 칸」에만 닿는다.
   - 선언이 늘어나 지평을 영구히 가리는 것을 막기 위해 선언 수를 매 실행 인쇄하고 `tests/test_rule_coverage_manifest.py` 매니페스트에 등재한다.
3. 마감: 1차 푸시 전(DART 접수 11/16 이후 수집 → 11/24 전후 푸시 목표)까지 설계·변이시험 통과. 그보다 늦으면 알려 주세요(1차 푸시가 밀립니다).

하지 말 것: 지평 파생 규칙(`_quarter_horizon.py`)을 「회사 수가 모자라면 분기를 빼는」 방식으로 완화(2026-08-29 사고의 재발 구조), `NB_CENSUS_MISSING` 등 owner 전용 등재를 이 티켓에서 미리 하는 것.

## 답변 (recipient 작성 — 처리 후)
