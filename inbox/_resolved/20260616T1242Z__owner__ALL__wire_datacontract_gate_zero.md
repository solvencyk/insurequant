---
from: owner
to: publishing
created: 20260616T1242Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 발주 (owner) — data-contract 게이트를 push 게이트 #0로 배선 (와이어링·publishing측)

validation이 만든 `scripts/validate_data_contract.py`를 **push 추천 직전 1순위(#0) 차단 게이트로 끼워넣어라.**

- publishing 게이트 순서(`claude-agent-publishing.md` §3)에 **#0 data-contract**를 기존 validation/assembly 게이트 **앞**에 삽입.
- **zero-RED 정책(owner 락)**: 게이트 exit≠0(RED≥1)이면 push 추천 = **BLOCKED**. **면제 없음** — `DATA_CONTRACT_EXCEPTION` 우회 금지. RED는 담당 stage가 고치거나 owner 에스컬레이션. (즉 §3.1 "RED=0 또는 TODO 문서화 예외" 조항은 data-contract 게이트엔 **미적용** — 0이어야 통과.)
- 실행은 풀패스 python. 게이트 리포트(사람이 읽는 형식)를 push 추천 리포트에 첨부.

### 주의
- python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`. 인라인 멀티라인 `python -c` 금지. `build_csm_waterfall_master.py` 실행 금지.

## 답변 (publishing 2026-06-16)

`claude-agent-publishing.md` §3 #0 gate 명문화 완료 (별도 validation inbox `1254Z` 처리와 동시 진행).
- #0 data-contract: `validate_data_contract.py` exit 2 = BLOCKED, exception 없음, owner 정책 명기.
- 현재 라이브 RED=52 = push BLOCKED 정상 (sensitivity_heatmap V12 stale, parser refill 대기).

status: resolved
