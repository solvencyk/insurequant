---
from: validation
to: parser
created: 20260615T0415Z
status: resolved
route: reparse
company: MULTI
period: 2025.4Q
rule: SENSITIVITY_REFILL
lane: ifrs17
iter: 1
---

## 미결 (validation 작성 — owner 지시: CSM 민감도 전수를 25.4Q 경영공시 기준으로 재추출)

**목표**: `sensitivity_heatmap.json`(IFRS17.html 6) 민감도 패널 소스)을 **25.4Q(2025.12.31) 경영공시(`data/disclosure/FY2025_Q4`) 기준으로 전수 재추출**. 현재는 **FY2024 DART 사업보고서(`data/dart/extracted/<사>_<rcept>_sensitivity.json`, 예 흥국생명 rcept 20250331003642 = 2024.12.31)** 기준이라 **1년 stale + 비전수**(비상장 보험사 DART 사업보고서 미제출).

**소스 결정 근거 (owner+validation)**: 경영공시 = 전 보험사 의무·분기별·장해질병 정액/실손 등 risk 세분 보유. DART 사업보고서 = 상장/대형사만·연 1회. → 전수 + 25.4Q + granular 목표엔 경영공시가 정답. (둘 다 2025.12.31 시점·~2026.3 제출로 recency는 동급, 커버리지·세분이 경영공시 우위.)

### 흥국생명 raw 분석 (현 파이프라인 진단 — 참고)
- 현 소스 FY2024 사업보고서 표 구조 = `[risk, shock, 상품구분(사망보험/건강보험/연금과저축보험/합계), 당기말 CSM, 손익효과, 자본효과, 전기말 …]`.
- **parser가 합계 행을 충실 추출**(해지율↑ 합계 CSM (144,520)=−1445.2억·손익 6,112=+61.12억 → heatmap 일치). **파싱오류 아님.**
- 단 **FY2024 사업보고서엔 사망/해지/사업비 3 risk뿐 — 장해질병(정액·실손) 행 부재**. 25.4Q 경영공시엔 존재 → 소스 교체로 해결.
- 해지율 역행(CSM↓·손익↑)은 source-faithful(건강보험 product CSM −112,242·손익 +564 견인).

### 요청 (전수 재추출 스펙)
1. **소스**: `data/disclosure/FY2025_Q4/raw/<KR>_*.pdf`(또는 parsed MD). 보험위험 민감도(보험계약마진/손익효과/자본효과) 표. **미다운로드면 inbox/downloader로 bounce**(refetch).
2. **시점**: **당기말(2025.12.31)만**. 전기말 컬럼 무시.
3. **risk 전수**: 경영공시에 있는 모든 shock 행 — 사망률 / 해지율 / 사업비·인플레 / **장해질병(정액) / 장해질병(실손)** / 기타. 누락 금지([[coverage-census-mandatory]]).
4. **컬럼 매핑**: `csm_delta`=보험계약마진(CSM) 변동, `pl_impact`=손익효과. 자본효과는 별도 컬럼(혼동 금지 — 흥국 자본효과 ≠ 손익효과). 괄호=음수.
5. **product 분해**: 상품구분(사망보험/건강보험/…)이 있으면 **합계 행을 risk-level 값으로** 채움(현 heatmap 컨벤션). product-level 보존은 designer와 별도 협의(F16 흥국 product-as-rows 이슈와 연계).
6. **단위 정규화**: 억원(경영공시 백만원이면 ÷100). 기존 `unit/unit_detected/unit_source` + OVER-scale 가드 유지. (validation SENSITIVITY_UNIT_SANITY도 또래-median 규모비로 교차감시.)
7. **coverage**: 경영공시에 CSM 민감도 표가 없는 회사 → `status: unavailable` 정직 표기(추측·가비지 금지). 25.4Q에 미공시면 직전 분기 fallback 여부는 owner 판단 큐.

### validation 측 신규 가드 (fill 후 자동 작동)
- **SENSITIVITY_DIRECTION_SANITY**(`validate_master_tables.py` 5b, 신설 2026-06-15, owner rule-of-thumb): `sign(csm_delta) ≠ sign(pl_impact)`면 YELLOW flag(|CSM|·|손익|≥1억 floor). 손익/자본 컬럼 오선택·부호오류를 전수 triage. **흥국 해지율형 source-faithful 역행도 flag되니, fill 후 각 flag를 real(onerous) vs 파싱오류로 판별 회신 바람.**
- SENSITIVITY_UNIT_SANITY(5): 또래-median 규모비 RED>1000x/YEL>100x.

회신 시 재추출 회사 수 + risk 행 수 + unavailable 명단 1줄 요약 → validation 재검증(direction/unit sanity 전수).

## SUPERSEDED (validation 2026-06-15)
소스 미결정 generic 발주였음. owner가 DART vs disclosure 판단 위임 → **disclosure(경영공시)·KICS lane으로 확정** + 흥국 raw 구조 검증 완료(602p, page 281/487, MD 부재, 8컬럼 이행현금흐름 오프셋). 대체: `20260615T0441Z__validation__MULTI_2025.4Q__csm_sensitivity_refill_from_disclosure_KICS`. 이 스레드 종결.

## 답변 (parser 작성 — 처리 후)
