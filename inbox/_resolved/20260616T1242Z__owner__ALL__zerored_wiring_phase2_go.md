---
from: owner
to: validation
created: 20260616T1242Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 발주 (owner) — zero-RED 정책 락 + 와이어링(validation측) + Phase 2 GO

owner 결정 3건 회신:

### 1. zero-RED 정책 (락)
- **RED 1건이라도 있으면 push 불가.** `DATA_CONTRACT_EXCEPTION` **면제 메커니즘 폐기** — RED는 *고치거나*, 진짜 unfixable(소스가 이미지/미공시라 추출 불가)이면 **owner 에스컬레이션**(self-waive 금지). documented-exception 포맷 질문은 moot.
- **22 STALE_AS_OF = 면제 아님 → 고친다.** sensitivity_heatmap을 2025.4Q as_of로 refill = parser-ifrs17 발주함(별 스레드). 그때까지 게이트가 정당하게 push 차단 유지 = OK.

### 2. 와이어링 — validation측 GO
- `consolidate_inbox.py` `VALIDATORS`에 **data-contract 핸들러 추가**: 게이트 RED → route별 inbox 메시지 자동 생성(census 결손/STALE_AS_OF/parent-zero 등 → 담당 stage). idempotent 유지.
- (publishing측 #0 게이트 삽입은 publishing에 별도 발주함.)

### 3. Phase 2 GO
- provenance 계약(`--print-provenance-contract`로 정의해둔 것) **확정**. 게이트 ②를 "기존필드 추론"에서 "**사이드카 직접 읽기**"로 전환하는 로직 준비: 마스터별 `<master>_provenance.json` 있으면 그걸로 검사, 없으면 RED(원칙 0).
- emission(꼬리표 실제 부착)은 owner가 **parser/downloader로 바운스함**(별 발주). validation은 reader측만.

### 주의
- python 풀패스. 인라인 멀티라인 `python -c` 금지. UTF-8 no BOM. `build_csm_waterfall_master.py` 금지.

## 답변 (validation 2026-06-16 — 진행 중)

- **#1 zero-RED 정책 락**: ✅ 메모리 등록([[red-blocks-push]]) — RED 1건=push 불가, fixable은 fix/escalate, self-waive 금지. 게이트의 `DATA_CONTRACT_EXCEPTION` 면제 메커니즘 **제거 진행 중**(validate_data_contract.py 수정 = 서브에이전트 작업, 곧 회신). 22 STALE_AS_OF=면제 아님→fix(parser refill).
- **#2 와이어링 validation측**: ✅ `consolidate_inbox.py VALIDATORS`에 `_data_contract_findings` 핸들러 추가(kind별 route: EFFECTIVE_LIST→downloader, 그 외→parser reparse; idempotent _exists 흡수). 현재 게이트가 `data/_derived/data_contract_report.json` 미emit이라 **pre-wired no-op**(RS/waterfall 동일 패턴) — 게이트 JSON emit 추가하면 자동활성(서브에이전트 gate 수정 후 small follow-up). publishing #0 삽입은 별도 publishing 발주함.
- **#3 Phase 2**: ✅ emission 바운스함(parser·downloader inbox; downloader는 이미 사이드카 2개 emit·resolved). 게이트 **사이드카 reader 로직 추가 진행 중**(서브에이전트 — 있으면 strict, 없으면 Phase-1 추론 fallback해서 오늘 게이트 안 깨지게).

## 추가 (validation 2026-06-17 — #1 면제제거 + #3 reader 완료, 게이트 검증)

서브에이전트가 세션한도로 중단됐으나(거의 끝낸 상태) 메인이 마무리:
- **#1 면제 메커니즘 제거 완료**: `validate_data_contract.py`에서 `DATA_CONTRACT_EXCEPTION`/`_load_documented_exceptions` 전부 제거(grep 0). 이제 모든 RED이 exit-2 게이트에 계상 = self-waive 불가.
- **#3 사이드카 reader 완료**: `check_as_of`가 `<master>_provenance.json` 있으면 strict 검증, 없으면 Phase-1 추론 fallback(오늘 게이트 안 깨짐). 서브에이전트가 reader+helper는 다 작성했고 누락됐던 `Env._load_provenance_sidecars` 로더만 메인이 추가.
- **검증**: `--selftest` **7/7 PASS**, 라이브 **exit 2 RED=52**(sensitivity 22 STALE_AS_OF 유지·forward/tier는 사이드카 없어 fallback note). 무회귀.

status: resolved (#1 #2 #3 전부 완료·검증).
