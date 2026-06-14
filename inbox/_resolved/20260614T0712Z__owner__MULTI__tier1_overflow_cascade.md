---
from: owner
to: publishing
created: 20260614T0712Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 미결 (sender 작성 — owner 라이브 사이트 QA) — 방법론 변경 [glitch G2]

**기본자본(Tier-1) 한도 소진율 100% 초과분을 보완자본(Tier-2)으로 cascade + forward outlook 소진 순서.**

사용자 지적: 기본자본 소진율이 100%를 넘으면 화면이 그냥 100%로 캡. 그러나 **초과분은 보완자본으로 인정**되므로, (a) 그 초과분을 보완자본 소진율에 가산하고, (b) forward outlook 계산도 **보완자본 먼저 소진 → 그다음 기본자본** 순서여야 함.

현재 상태(증거):
- `scripts/compute_tier1_utilization.py` ~line 396-405: tier1 초과분(recognized−limit) **버려짐**. overflow 필드 없음.
- `scripts/compute_tier2_utilization.py` ~line 274-313: tier2 분자 독립 계산, tier1 spillover 미반영.
- `scripts/forward_capital_simulation.py` ~line 356-390: 채권 차감이 tier 구분 없이 균일 → tier2 우선소진 우선순위 없음.
- 예: KR1000 tier1 242.5%(초과 142.5%p)인데 tier2 반영 0. (KR0032 187%, KR0073 171% 등도 해당.)

권장 조치 (backlog → 계산 파이프라인):
1. compute_tier1_utilization.py: `tier1_overflow_eok = max(recognized − limit, 0)` 출력 추가.
2. compute_tier2_utilization.py: tier1 overflow를 tier2 분자에 가산.
3. forward_capital_simulation.py: 채권을 tier 우선순위(후순위/tier2 먼저)로 정렬·차감, 소진 tier 추적.
4. DAG: TIER1_JSON(overflow) → TIER2_JSON(가산) → FORWARD_DATA(tier 우선순위) 재생성.
- 표시(K-ICS.html 100% 캡, "XXX%+" + 보완자본 가산 툴팁)는 designer inbox에 한 세트로 올림.

방법론 확인 포인트: K-ICS 규정상 기본자본 초과분의 보완자본 인정 한도/조건(보완자본 자체 한도 있음) 반영 — domain 검토 후 구현 권장. 불명확하면 escalate(사람 큐).

## 답변 (publishing 작성 — 2026-06-14 처리)

**근본 원인 재진단 → cascade 미채택, 파서로 라우팅 (owner 승인).**

- 규정 확인(K-ICS 해설서 [별표22] Ⅲ.2): ① 기본자본 자본증권 인정한도 = SCR×10%(조건부자본증권 15%), 초과분 보완자본 재분류(다.(1)). ② 보완자본 한도 = SCR×50%(마.) — **이미 tier2 스크립트 분모(`scr*0.5`)에 반영됨.**
- **핵심 발견**: tier1 100% 초과 9개사 전부 `excess`(Ⅴ.1 재분류액) 파싱 누락. excess만 추출되면 `recognized=limit` → 소진율 정의상 ≤100%. 현재 >100%는 **파싱 artifact**이지 실제 초과자본 아님.
- **cascade 미채택 사유**: 공시 보완자본(라.(1))에 재분류분이 이미 포함 → publishing에서 tier2 분자 가산 시 **이중계상**.
- **조치**: parser(kics) inbox에 excess 추출 보강 요청 → `inbox/parser/20260614T0755Z__publishing__MULTI_2025.4Q__tier1_hybrid_excess_unparsed.md` (route: reparse, 부재 시 blind_spot).
- **보류**: compute_tier1/tier2/forward_capital 코드 변경 안 함. 파서 excess 추출 후 재계산 → tier1 캡 정상화 확인 → 그때 designer 표시(소진율 100% + "신종 X억 중 Y억 보완자본 재분류" 주석) 핸드오프.

→ owner 재확인용 status: answered. 파서 응답 후 publishing 재계산 트리거.

## 종결 (publishing 2026-06-14 — 파서 회신 반영, 구현 완료 → resolved)

파서 회신: standalone Ⅴ.1 행 9사 전부 부재, 번들행("…초과한 금액 **등**")으로만 공시 → blind_spot. 번들값 검산상 신종 한도초과분과 40배 차이(번들="등" 기타항목, 신종초과분은 공시 보완자본에 직접 반영). owner 결정(가랏): **소진율 100% 캡(옵션 2/3) 채택.**

구현(`compute_tier1_utilization.py`): `utilization_pct=min(recognized/limit,1.0)*100` 캡 + `tier1_hybrid_overflow_eok=max(recognized−한도,0)` 신설(보완자본 재분류분 명시). 9사 util15 → **전부 100.0**, util>100=0건. `templates/tier1_utilization_latest.json` 갱신(K-ICS.html 리더). **tier2/forward_capital 무변경**(cascade 이중계상이라 미채택 — owner 합의). 파서·designer inbox 정리 완료.
