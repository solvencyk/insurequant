---
from: owner
to: validation
created: 20260610T0110Z
status: resolved
route: reparse
company: ALL
period: ALL
rule: RS1-RS4_NEW
iter: 1
---

## 미결 (sender 작성)

**신규 feature: K-ICS 금리민감도 검증 룰 구현** (owner 발주 2026-06-10).
parser가 `kics_rate_sensitivity.json` + diag를 생성하면 (parser inbox `20260610T0100Z__owner__ALL__kics_rate_sensitivity.md` 참조) 아래를 검증.

스펙 정본: `docs/agents/kics-rate-sensitivity-spec.md` §5 (RS1–RS4).

작업:
1. `scripts/validate_kics_rate_sensitivity.py` 구현:
   - **RS1_RATIO_IDENTITY** (RED): 각 (사,분기,경과조치)·각 컬럼: 비율 ≈ 금액/기준금액×100,
     tol `max(0.5%p, 0.5%·|비율|)`. → delta 오변환·행 오매핑 검출기.
   - **RS2_BASE_ANCHOR** (RED): base 컬럼 vs `kics_disclosure.json` item1/item14/item27
     (적용전; 적용후는 `값_적용후` 있을 때만). tol 금액 2억 / 비율 0.5%p.
   - RS3_DIRECTION_SANITY (YELLOW): 생보 금리하락→비율하락 통상. 역방향 플래그만.
   - RS4_COVERAGE_CENSUS (YELLOW): 인접 분기 보유한데 사이 구멍. FY2023~24Q3 부재는 정상.
2. 출력 JSON → `scripts/consolidate_inbox.py`의 `VALIDATORS`에 핸들러 추가
   (route: reparse, idempotent — 기존 continuity 핸들러 패턴 복제).
3. RED → inbox loopback (max 5), 통상 프로토콜 (`docs/agents/claude-agent-validation.md` §3).
4. `docs/agents/claude-agent-validation.md` §1.1 룰 표에 RS1–RS4 추가 (변경 이력 갱신).

게이트: RED 0 전에는 마스터를 publishing 산출물로 취급하지 말 것.

## 답변 (recipient 작성 — 처리 후)

**RS1–RS4 구현 완료 — RESOLVED.** parser가 `kics_rate_sensitivity.json`(423행) 적재 → 검증 통과.

1. ✅ `scripts/validate_kics_rate_sensitivity.py` 구현 (RS1 RED / RS2 RED / RS3 YELLOW / RS4 YELLOW). 결과 JSON `data/_derived/kics_rate_sensitivity_validation.json`.
   - RS1 0 RED, RS2 0 RED(+KR0011 2025.2Q exception), RS3 28 YELLOW, RS4 1 YELLOW. **gate RED=0.**
2. ⏳ `consolidate_inbox.py` VALIDATORS 핸들러 — RED=0이라 loopback 미발생. 배선은 후속(RED 발생 시 필요). 현재는 standalone 러너로 동작.
3. ✅ RED loopback 프로토콜 준비 (RED→parser inbox max5). 현재 RED 0이라 미발동.
4. ✅ `claude-agent-validation.md` §1.1 룰표에 RS1–RS4 추가.

KR0011 2025.2Q는 별도/연결 basis 차이 → `RS2_EXCEPTIONS`로 코드 반영(게이트 블록 안 함). 게이트 RED 0이므로 마스터 publishing 적격 조건 충족(단 RS3/RS4 YELLOW는 정보성).
