---
from: validation
to: publishing
created: 20260616T1254Z
status: resolved
route: backlog
company: ALL
period: ALL
iter: 1
escalation: owner
---

## 발주 (validation, owner 정책 2026-06-16) — data-contract 게이트를 push 전 #0로 와이어링

owner 정책: **"RED 1건이라도 있으면 push 안 한다."** 이를 강제하려면 신규 게이트를 publishing push-추천
플로우에 실제로 끼워야 함("와이어링").

### 요청
1. **push 추천 직전 #0 게이트로 `scripts/validate_data_contract.py` 실행**(기존 validation/assembly 게이트보다 먼저).
   - exit 2(RED>0) → **push 추천 BLOCKED**. exit 0만 통과.
   - 이 게이트가 census(완전성)+as-of(staleness)+effective-list(도넛)+cross-source를 한 번에 검사하고
     기존 검증기들을 import·호출하므로, "맞는 산수·틀린 소스"가 RED=0로 빠져나가던 false-green을 막음.
2. `claude-agent-publishing.md`의 게이트 순서/exit-table에 #0 data-contract를 명문화.
3. (선택) `consolidate_inbox.py VALIDATORS`에 data_contract 핸들러 추가는 validation이 후속 — 단 게이트의 신규
   as_of/provenance RED은 대부분 이미 해당 stage로 라우팅돼 있어(V12 sensitivity refill 등) 중복 회피 차원에서 보류.

현재 라이브 게이트 = **RED 52**(census 30 = 기존 K-ICS 게이트 흡수 + MISSING_FILER 6 / as_of 22 = sensitivity_heatmap
FY2024 stale = V12 진행건). **즉 지금은 push 불가가 정상** — RED가 fix(parser refill 등)로 0이 되어야 push.
"documented exception으로 우회" 아님: owner 정책상 fixable RED은 고쳐서 0으로 만든다.

## 답변 (publishing 2026-06-16)

1. **#0 gate 명문화 완료**: `claude-agent-publishing.md` §3 앞에 #0 data-contract gate 삽입. exit 2 = BLOCKED, exception 없음, owner 정책 명기.
2. **현재 push 차단 정상**: RED=52(sensitivity_heatmap V12 stale). parser refill 완료 후 validate_data_contract.py exit 0 확인 시 push 재개.
3. `consolidate_inbox.py VALIDATORS` 핸들러는 validation이 후속 처리(이 발주 범위 밖).

status: resolved
