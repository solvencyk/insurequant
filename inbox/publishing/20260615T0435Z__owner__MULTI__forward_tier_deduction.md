---
from: owner
to: publishing
created: 20260615T0435Z
status: answered
route: backlog
company: MULTI
period: forward (2026~)
iter: 1
---

## 미결 (sender 작성 — owner)

**forward outlook 시뮬에서 신종자본증권 call/만기분 제거 시 차감 순서 = 보완자본(Tier-2) → 기본자본(Tier-1).** (owner 명제 확정, 규정상 타당.)

근거(재분류 정의상 자동):
- 매 시점: 신종 잔액 `H`, 기본자본 인정한도 `L = SCR×10%`(조건부/신종 15%). 기본자본 기여 `min(H,L)`, 보완자본 기여 `max(H−L,0)`.
- 신종 `c` call 제거 → `H−c`로 min/max **재계산**:
  - `H−c ≥ L`(초과분 잔존): 차감 전액 **보완자본에서만**, 기본자본 불변.
  - `H−c < L`(초과분 소진): 보완자본 0 → 나머지 **기본자본**에서.
- = "보완 먼저, 그다음 기본"이 그대로 나옴. **별도 순서 분기 불필요 — 매 시점 H 갱신 후 min/max 재계산이면 끝.**

작업: `scripts/forward_capital_simulation.py` (~line 356-390 채권 차감부)에 위 로직 구현. 채권 call/만기 스케줄 = `data/bonds/normalized` + `scripts/normalize_bond_schedule.py`. **신종자본증권(hybrid, 이 로직)과 후순위채(순수 Tier-2) 구분.** 시점별 SCR로 L 산출.

검증: 신종 call 도래 회사(예 KR1000)로 forward 1회 돌려 tier2 먼저 소진→tier1 순인지 확인. Windows 인라인 `python -c` 금지, python 풀패스.

연계: 도넛 "100%+" 표시 = designer inbox `20260615T0435Z__…kics_tier1_donut_100plus.md`. (이건 발행/한도 표시, 이 차감로직과 별개.)

## 답변 (publishing 2026-06-15 — 구현 + 검증 완료)

`scripts/forward_capital_simulation.py` 구현 완료 (owner 알고리즘 그대로):
- 상수 `HYBRID_LIMIT_RATIO=0.15` 추가. 루프 전 `total_hybrid` 산출.
- 차감부 교체: `scr_y` 먼저 계산 → `limit_y=scr_y×0.15`, `hybrid_remaining=total_hybrid−누계신종call`, `hybrid_t1=min(H,L)`, `hybrid_t2_overflow=max(H−L,0)`. **`basic_y = basic_baseline + (min(H_y,L_y) − min(H_0,L_0))`** = 매 시점 재계산 → 별도 순서분기 없이 T2-first 자동.
- 후순위채(tier2_subordinated)는 총자본만 차감, 기본자본 불변(유지). 출력에 hybrid_remaining/tier1/tier2_overflow/limit 진단필드 추가.

**검증 (KR1000 코리안리, 신종 8,100억·L=3,333):**
| yr | 신종call누계 | H | T1=min(H,L) | T2초과 | 기본자본 |
|---|---|---|---|---|---|
| 2026 | 0 | 8100 | 3333 | 4767 | 35582 |
| 2027 | 3300 | 4800 | 3333 | **1467** | **35582 불변(T2만)** |
| 2028 | 5800 | 2300 | 2300 | **0** | **34550 ↓(T1 시작)** |
| 2029 | 8100 | 0 | 0 | 0 | 32250 |
→ **T2 먼저 소진 → T1 순서 확인.** 규정 [별표22] Ⅲ.2.다.(1) 정합.

빌드 1회 실행: `output/kics_forward_capital/20260615T050803Z/forward_simulation_v3.json` + `templates/forward_capital_latest.json` + **K-ICS.html `window.FORWARD_DATA` 동기화**(37사 ok). 배포(K-ICS.html)는 owner GO 대기. status: answered.

연계: 도넛 "100%+" 표시는 designer inbox 별건(이 차감로직과 무관). 확인.
