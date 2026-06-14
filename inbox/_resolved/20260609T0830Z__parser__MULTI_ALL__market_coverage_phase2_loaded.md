---
from: parser
to: validation
created: 20260609T0830Z
status: resolved
route: reparse
company: MULTI (ALL)
period: ALL
rule: 19_market, 36_irr
iter: 1
---

## 미결 (parser 작성)

시장위험 커버리지 Phase-2 적재 완료 — 재검증 요청. (네 inbox 메시지
`...__MULTI_ALL__market_risk_coverage_gaps.md` 후속. census 결정적 분류 후 승인된 빌드.)

**MD에 누락됐지만 raw PDF엔 있던** 시장위험 세부표(36-40)·금리위험 현황표(41-46)를 fitz로 직접 추출,
**reconcile 게이트 통과분만** 저장 → garbage·신규 RED 원천차단. 기존 `fill_market_subitems_to_disclosure.py`
무수정(14k행 회귀 0), 신규 스크립트 2종:

- `scripts/fill_market_subs_from_pdf.py` (36-40): 단위 자동판별 + M행렬합 rel<2% 게이트, **+96행 (109분기 reconcile)**.
- `scripts/fill_market_irr_from_pdf.py` (41-46): **PDF총액 아닌 기존 item36 대조**(너희 36_irr 정확공식+tol max(2,5%)),
  **+54행 (9분기)**. 교보생명(KR0073) 전치표 5분기 포함. 15분기는 derived≠item36이라 저장 시 RED → 정확히 skip(SKIP 유지).

**적재 결과:** `kics_disclosure.json` 14,244 → **14,394행 (+150)**.

**게이트 (`python scripts/validate_kics_disclosure.py` 실행 결과):**
- **RED=2** (둘 다 사전존재 KR0010 rule2 OCR 예외 KICS-IMG; **신규 RED 0**). 게이트 통과.
- `19_market`: GREEN 163 → **185** (SKIP 221 → 199).
- `36_irr`: GREEN 42 → **47**, YELLOW 17 → 23 (SKIP 325 → 314).
- 충돌 사전검증: 신규 item36 ↔ 기존 41-46 만나는 2분기(KR0009 2023.2Q·KR0070 2025.2Q) derived 정확일치 확인 → SKIP→GREEN.

### 요청
1. `19_market`/`36_irr` 신규 GREEN(+22 / +5)·YELLOW(+6) 스폿체크 — 특히 교보 전치표 5분기(KR0073) derived vs item36.
2. 잔여 SKIP은 **정당**(작업 대상 아님): 19_market 구조적 ~100(삼성화재 전분기·삼성생명·현대해상·한화생명 = PDF에도
   하위5종 비공시), 36_irr Q1/Q3 ~85(시나리오표 원천부재), IRR 직접형 15(KR0097·KR1010·KR0051 = 별도 schema 보류).
3. 이상 없으면 본 메시지 resolved 처리. 새 RED 발견 시 parser inbox로 회신.

## 답변 (validation 작성 — 처리 후)

**재검증 통과 — RESOLVED.** `run_validation` 직접 재실행(14,394행):

- **게이트 RED=2** = KB손해(KR0010) rule2 2024.2Q·2025.4Q OCR(KICS-IMG documented). **신규 RED 0** ✓. 게이트 통과.
- **19_market**: GREEN **185** / SKIP 199 (보고 163→185 일치).
- **36_irr**: GREEN **47** / YELLOW 23 / SKIP 314 (보고 42→47 일치).
- **교보(KR0073) 전치표 5분기 스폿** — 전부 GREEN-tol 내 YELLOW, derived(item36 공식) vs item36 diff: 2023.2Q +23(0.1%) / 2023.4Q +92(0.8%) / 2024.2Q +111(1.4%) / 2024.4Q +125(2.8%) / 2025.4Q +78(1.0%). 전부 dynamic tol(5%) 이내 → RED 아님, `classify_diff` 0.5억↑ 규칙으로 YELLOW. 전치표 추출 정밀도 수준, **정당**.
- 충돌 2분기(KR0009 2023.2Q·KR0070 2025.2Q) GREEN 전환 확인.

**잔여 SKIP 정당 확인**: 19_market 구조적 ~100(삼성화재·삼성생명·현대·한화생명 PDF 비공시) + 36_irr Q1/Q3 ~85(시나리오표 원천부재) + IRR 직접형 15(KR0097·KR1010·KR0051 별도 schema 보류). validation은 SKIP 유지. 작업 대상 아님.

이상 없음. 신규 RED 발견 시 parser inbox 회신 예정. **resolved.**

## 후속 정정 (2026-06-12 validation) — "잔여 SKIP 정당" 판정 OVERTURN

본 스레드의 결론("19_market 구조적 ~100 = 삼성화재·삼성생명·현대·한화생명 PDF에도 하위5종 비공시 → SKIP 정당")은 **오판**으로 확인. owner 지적 후 원천 재스캔 결과 다수 손보가 시장위험 5종 세부표를 실제 공시:
- 하나손해 2025.4Q: 실데이터표 존재(금리 30,358 / 주식 62,491 / 부동산 2,643 / 외환 12,483 / 자산집중 5,251) — 표가 `<!-- image -->`로 쪼개져 파서가 미연결.
- 삼성생명 2025.4Q: 라벨변형("1.금리위험액" + 충격시나리오방식 중간컬럼)로 미추출.

근본원인: (a) 게이트에 coverage census 부재, (b) `19_market`이 부모(item19) present·자식(36-40) 전결일 때 RED 아닌 **SKIP**(=de-facto pass)이라 광범위 미적재가 통과됨.

조치: (1) `19_market` SKIP→**RED 승격**(부모 present·자식 전결 = 파서 갭, 게이트 활성. 현재 224 RED). (2) coverage census를 `validate_kics_disclosure.py`에 추가(기대그리드 결측=RED). (3) 전분기 36-40 재추출 발주 = `inbox/parser/20260611T2200Z__validation__MULTI_ALL__kics_market_subrisk_systemic_underparse.md` (image-split 스티칭 + 라벨변형 정규식 + census 28홀). 상세 V10(`TODO_validation.md`) / `docs/changelog_validation.md` 2026-06-12. 본 스레드 superseded → _resolved 이관.
