---
from: owner
to: publishing
created: 20260619T0412Z
status: open
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 발주 (owner) — pre-push 게이트 #0를 prepush_check 체인 + LLM-skeptic 단계로 배선

owner 결정(2026-06-19): 두더지잡기 자동화 = **push 직전에만** 도는 깔때기. publishing §3 게이트 순서를 아래로 갱신.

### #0 = `python scripts/prepush_check.py` (기존 validate_data_contract 단독 호출 대체)
- 한 방에 ① data-contract 하드 게이트 + ② generic-anomaly triage 체인 실행.
- **exit 2(gate RED≥1) → push 추천 BLOCKED**(zero-RED, 면제 없음). 산출: `data/_derived/anomaly_triage.json`(리뷰 큐) + `anomaly_skeptic_input.json`(REAL+UNCERTAIN).

### push 직전 필수 단계 — LLM-skeptic (publishing 에이전트가 수행)
- `anomaly_skeptic_input.json`의 REAL+UNCERTAIN을 **publishing 에이전트가 적대적으로 검토**(또는 skeptic 서브에이전트 spawn): 각 후보를 **EXTRACTION_ERROR / UNIT_ERROR / REAL_EVENT / NOISE**로 분류.
- **EXTRACTION_ERROR·UNIT_ERROR → parser inbox 발주**(lane: ifrs17, CSM_waterfall/PL는 DART). REAL_EVENT·NOISE → 통과.
- **이 skeptic 단계 미수행 시 push 추천 금지**(게이트의 마지막 정밀층).
- 판단 컨텍스트: 마스터 전 분기 series + 메모리 `reference_kics_company_quirks`(이미지사·micro 등). (참고 verdict 1회분: `data/_derived/anomaly_skeptic_verdict.json` — orchestrator가 생성해둠.)

### 주의
- push-time only(주기 cron 아님). python 풀패스. 인라인 멀티라인 `python -c` 금지. `build_csm_waterfall_master.py` 금지.

## 답변 (publishing 2026-06-20)

완료. `docs/agents/claude-agent-publishing.md` §3 게이트 #0 업데이트:
- `validate_data_contract.py` 단독 호출 → `prepush_check.py` (체인) 교체
- LLM-skeptic 필수 단계 추가 (EXTRACTION_ERROR/UNIT_ERROR → parser 라우팅, REAL_EVENT/NOISE → 통과)
- 현재 라이브 RED=4 (CHECK4: T2_UTIL×3 + T2_DENOM×1) 명시
- 참조 verdict 파일 (`anomaly_skeptic_verdict.json`) 경로 명시

status: answered
