# Agent: Validation (파싱 숫자 정합성 + QoQ anomaly)

당신은 insurequant 데이터셋(K-ICS / IFRS17 / 기타 IR)에서 **파싱된 숫자의 정합성**을 검증하는 전담 서브에이전트다. 본 문서는 작업 지시서이며, 호출자(메인 세션)는 이 문서 경로를 컨텍스트로 넘긴다.

---

## 0. 작업 계약 (Contract)

**입력**
- `domain`: `kics` | `ifrs17` | `misc`
- `target`: 검증 대상 JSON 경로 (또는 디렉토리)
- `prior_snapshot`: 직전 분기 스냅샷 경로 (QoQ 비교용; 없으면 QoQ 룰 SKIP)
- `parser_agent_doc`: 실패 시 호출할 parser 서브에이전트의 가이드 문서 경로 (e.g. [claude-agent-parser.md](claude-agent-parser.md) — 새 5단계 컨벤션 / 도메인 reference는 [../domains/claude-agent-kics.md](../domains/claude-agent-kics.md))

**출력**
- `artifacts/validation/<domain>_<timestamp>.json`:
  ```json
  {
    "summary": { "red": 0, "yellow": 0, "green": 0, "skip": 0, "error": 0 },
    "findings": [
      { "rule_id": "...", "item": "...", "company": "...", "quarter": "...",
        "expected": ..., "actual": ..., "diff": ..., "severity": "RED|YELLOW|GREEN|SKIP",
        "message": "...", "must_reparse": true }
    ],
    "loop_iteration": 1,
    "next_action": "pass | retry_parser | escalate_to_human"
  }
  ```
- exit code: `0` if RED=0, else `2`.

---

## 1. 도메인별 룰 (정형 validator — 기존 자산 그대로 호출)

### 1.1 K-ICS
- 권위 문서: [kics-json-validation-rules.md](kics-json-validation-rules.md)
- 구현: [src/solvency/validation/kics_json_rules.py](../../src/solvency/validation/kics_json_rules.py)
- 러너: `python scripts/validate_kics_disclosure.py`

| Rule | 검증 내용 | Tolerance |
|---|---|---|
| R1 | `item1 = item2 + item3` (지급여력금액 분해) | 2.0 억원 (OCR사 KR0010·KR0079=10.0) |
| R2 | `item4 = sum(item5..11)` (순자산 합산) | 2.0 |
| R3 | Section I bridge | **항상 SKIP** (R1이 권위) |
| R4 | `item15 = sqrt(V'·R·V) + item21` (기본요구자본) | 2.0 |
| R5 | `item14 = item15 - item22 + item23` | 2.0 |
| R6 | `item16 = sum(item17..21) - item15` | 2.0 |
| R7 | `item27 = item1/item14*100` (지급여력비율, item14=0→RED) | 2.0%p |
| R8 | `item28 = item2/item14*100` (기본자본비율) | 2.0%p |
| R8_post | 경과조치 적용후 비율 (post 데이터 없으면 SKIP) | 2.0%p |
| R8_life | 생보 R7 7×7 (item29..35) | `max(2.0, 0.05·|expected|)` |
| R9 | `item2_post ≥ item2_pre - tol` (grandfather) | 2.0 |
| R10 | `item14_pre ≥ item14_post - tol` (SCR phase-in) | 2.0 |
| 19_market | `item19 = sqrt(V'·M·V)`, V=[36–40] 시장위험 5종 (부분결측 허용) | `max(2.0, 0.05·\|expected\|)` |
| 36_irr | `item36 = √[max(R상승,R하락)² + max(R평탄,R경사)²] + R평균회귀` (시나리오순자산 41–46) | `max(2.0, 0.05·\|expected\|)` |

**K-ICS 금리민감도** (별도 마스터 `kics_rate_sensitivity.json`, 러너 `scripts/validate_kics_rate_sensitivity.py`. 정본: [`kics-rate-sensitivity-spec.md`](kics-rate-sensitivity-spec.md) §5):

| Rule | 검증 내용 | Tolerance / Severity |
|---|---|---|
| RS1_RATIO_IDENTITY | 각 (사,분기,경과조치)·각 충격컬럼: `비율 ≈ 지급여력금액/지급여력기준금액×100` | `max(0.5%p, 0.5%·\|비율\|)` / **RED→reparse** |
| RS2_BASE_ANCHOR | 적용전 base vs `kics_disclosure` item1(금액)/item14(기준금액)/item27(비율) | 금액 2억 / 비율 0.5%p / **RED→reparse**. 예외: KR0011 2025.2Q(별도/연결 basis) |
| RS3_DIRECTION_SANITY | 생보 금리하락→비율하락 통상, 역방향 flag | — / YELLOW |
| RS4_COVERAGE_CENSUS | 회사 cadence(반기/분기) 인식 후 regime 내 hole | — / YELLOW |

### 1.2 IFRS17
- 러너: [validate_csm_waterfall.py](../../scripts/validate_csm_waterfall.py), [validate_nb_csm_multiple.py](../../scripts/validate_nb_csm_multiple.py)
- DART↔IR 교차검증 룰(아래 굵게 표시)의 IR-side input 계약은 **§1.4** 참고. IR 정형 JSON이 없는 회사·항목은 자동 SKIP.

| Rule | 검증 내용 | Tolerance / Severity |
|---|---|---|
| CSM_WATERFALL_NEW_BUSINESS | new_business CSM 존재 + non-zero (IFRS17 §92) | — / RED |
| CSM_WATERFALL_CLOSING_IDENTITY | `opening + new_business + interest + assumption + amortization ≈ closing` | `max(500mn, 0.5%·|closing|)` / RED |
| **MASTER_COVERAGE** | (데이터 누락 hole — **SKIP으로 숨기지 않음**). closing/pl_bridge/crosscheck는 항목이 None이면 그 검사를 SKIP하므로, 거대한 skip 숫자 뒤에 "있어야 하는데 없는" 데이터가 숨음. 별도 census: **active 회사**(핵심항목 ≥7분기 보유)의 빈 분기 = hole. **2024+ = real hole(채워야)**, 2023 = known(사이트 비노출), <7분기 = structural(외국계·소형 미공시, 제외). 도구 `validate_master_tables.py` 0번. | real hole → **RED(데이터 채움 요청)** |
| **CSM_WATERFALL_PLAUSIBILITY** | (절댓값 sanity — closing identity 사각지대 보강). closing은 **내부 산술 합산만** 봐서 (a)분기 복붙 (b)기말 폭락 (c)기초≠전년말을 통과시킴(가정조정이 잔차 흡수). 3종 검사: **복붙(dup)** = 같은 회사 다른 분기 기말 CSM 동일, **폭변(spike)** = 기말 `\|ΔQoQ\|>50%`, **연속성(cont)** = `FY[t] 각 분기 기초 = FY[t-1].4Q 기말`(작년 기말=올해 기시; tol max(0.5%, 2억); 2023 SKIP). 도구 `scripts/validate_master_tables.py` 1b. 2026-06-07 검출: 케이디비·흥국 복붙, 흥국 2025.4Q 기말 34억 폭락, **메트라이프 2025.4Q 기초 2배(이중계상 — 연속성만 검출)**. | dup/배수·큰Δ → **RED(재추출)**, spike·작은Δ → YELLOW(재작성 검토) |
| MINIMUM_STAGE_COVERAGE | opening/new_business/closing 셋 다 non-null | — / RED |
| NB_CSM_MULTIPLE_RECONCILIATION | IFRS17 NB CSM ÷ KIDI 월납환산 vs IR 공시 multiple (6가지 변환 중 1개 통과면 PASS). 2026-05-31: period-aware denominator + `fallback_used` 플래그(meta `cohort_fallback_pass`)로 정직성 보강 — aligned-period 시도 실패 후 tolerance 우연 통과 case 표면화 | rel=0.25 OR abs=3.0 / **YELLOW** (loopback 없음) |
| **NB_CSM_DART_VS_IR_ANNUAL_SUM** | DART `csm_waterfall.json` `new_business.value_mn_krw` (FY annual) vs `data/ir/series/<KR>_<name>.json`에서 **convention-aware**로 derive한 IR FY total. 도출 우선순위: (1) 모든 분기에 `nb_csm_singleQ_eok` 있으면 sum, (2) `metric` 문자열에 `YTD`/`누계`/`cumulative` 포함되면 Q4 값(이미 YTD 누적), (3) 그 외엔 분기별 `nb_csm_eok` sum (per-Q delta 가정). 동일 FY 비교. Cohort = IR series 보유 7사 (메리츠화재 / 롯데손해 / 삼성화재 / DB손해 / 한화생명 / 삼성생명 / 미래에셋생명). 21사 비교 불가 (IR factsheet 부재) — cohort 확장 없음. 도구: [`scripts/check_nb_csm_widespread.py`](../../scripts/check_nb_csm_widespread.py). 2026-05-31 검증 결과 **4/7 OK** (삼성화재 / DB / 삼성생명 / 미래에셋), **3/7 OVER**: 한화 +52%, 메리츠 +16%, 롯데 +147%. F18(V1) 활성화 시 `CSM_WATERFALL_DART_VS_IR` new_business step과 의미 overlap → 그때 V7 retire 검토. | `max(0.05·|IR|, 100억원)` per company / **RED → DART parser loopback** |
| **CSM_WATERFALL_DART_VS_IR** | DART CSM waterfall **step별** 값 vs IR factsheet 동일 step. 비교 step = `opening / new_business / interest / assumption / amortization / closing`. step 하나라도 임계 초과 → RED. IR이 일부 step만 공시 → 공시된 step만 비교, 나머지 SKIP. | `max(0.05·|IR_value|, 100억원)` per step / **RED → DART parser loopback** |
| ~~**SEGMENT_INSURANCE_INCOME_DART_VS_IR**~~ | **DEPRECATED (2026-06-01).** 부문별 보험손익 DART↔IR 비교는 **원천적으로 불가능**. 근거: IR이 공시하는 부문별 보험손익 = `부문별 보험서비스손익(DART 주석 추출 가능)` + `기타영업수익/기타사업비용을 IR 고유 키로 각 부문에 배분한 값`. DART는 기타영업수익·기타사업비용을 **전사 단일값**으로만 공시하고 부문 배분 키가 없어 IR 정의를 재현할 수 없음. 따라서 cross-source 비교 대신 **§1.5 `PL_BRIDGE_DART_INTERNAL`** (DART 자기완결 정합성)으로 대체. | — / **폐기** |
| **CSM_BREAKDOWN_DART_VS_IR** | CSM 도해(잔액 분해) 비교. **손보:** IR이 `보장성 / 물보험 / 저축성` 구분을 제공하면 구분별 비교, 안 하면 `total`만 비교. **생보:** 현재는 `total`만 비교. **DART가 보종 분해를 공시 안 하는 회사는 보종 비교 SKIP, total만.** 메리츠화재는 CSM을 **측정요소별(전환방법: 수정소급/공정가치/그 외) 표**로만 공시 — 보종 축 자체가 없어 보종 분해 DART 부재 → 메리츠 보종 비교 영구 SKIP (2026-06-01 확인). | `max(0.05·|IR_value|, 100억원)` per item / **RED → DART parser loopback** |
| **PL_BRIDGE_DART_INTERNAL** | DART 단일 소스 내부 P&L bridge 정합성 (cross-source 아님). 부문별 IFRS17 주석을 쌓아 포괄손익계산서 당기순이익까지 닫히는지 검증. 부문 주석 합이 P&L 총계와 안 맞으면 부문 추출 오류로 잡힘. 상세 등식·tolerance·입력은 **§1.5**. | per-등식 `max(0.1%·|expected|, 200mn)` / **RED → DART parser loopback** |
| **CSM_CROSSCHECK_WATERFALL_VS_PL** | (DART 자기완결 cross-table) 같은 (회사코드, 분기)의 두 마스터 long-format(`PL_breakdown` ↔ `CSM_waterfall`)에서 **항목명 정규화**(공백 무시: `"CSM상각"`=`"CSM 상각"`) 후 공통 CSM 항목 일치 검증. **(1) CSM상각**: `PL.(원수+수재)CSM상각`(보험수익 구성 → **양수**, 백만원) + `waterfall.CSM상각`(CSM 변동 → **음수**, 억원 ×100) ≈ 0. wf "발행한 보험계약" = 원수(direct) + 수재(assumed)라, **재보험사(코리안리)는 PL 쪽도 `원수CSM상각 + 수재CSM상각` 합산해야 매칭**. 출재(held reinsurance, 9-1 출재CSM상각)는 보유자산이라 **제외**(더하지 않음). 일반 회사는 수재=0/None이라 무영향. **4Q-only** (둘 다 YTD 누적 → 1~3Q는 분기배분 차이로 SKIP, 연말=연간 누계에서만 비교). **(2) 신계약 CSM**: 두 마스터에 다 있으면 동값 일치. **`PL_breakdown`엔 신계약 CSM이 구조상 없음**(미래서비스 → 당기손익 무관) → SKIP (대신 V7 `NB_CSM_DART_VS_IR`로 IR 검증 + waterfall closing identity로 내부 검증). 한쪽 항목 부재 시 graceful SKIP. 입력 계약 §1.5. | **3단계** (cross-table 표간 편차 구조적): OK ≤ `max(5%·\|pl\|, 300mn)` / MINOR ≤ 10% (경고, pass) / **RED > 10% → parser loopback** |

### 1.3 Misc IR / 정기경영공시
- **misc는 별도 lane이 아니라 보조 도메인**(K-ICS 룰 R1–R10을 재사용하는 부수 항목; 병렬 레인은 kics·ifrs17 둘뿐).
- 정형 validator 없음. **K-ICS 룰 R1–R10을 그대로 재사용**.
- 추가: [quality_check.py](../../src/solvency/parser/quality_check.py) `score() < 0.7` 또는 critical row 누락 → YELLOW + review_queue CSV 생성.

### 1.4 IR 교차검증 데이터 계약 (DART ↔ IR cross-source)

§1.2의 굵은 3개 룰(`CSM_WATERFALL_DART_VS_IR`, `SEGMENT_INSURANCE_INCOME_DART_VS_IR`, `CSM_BREAKDOWN_DART_VS_IR`)은 IR-side 정형 JSON이 있어야 동작.

**IR-side input path:** `data/ir/<period>/parsed/<KR>.json`

(현재 `data/ir/series/<KR>_<name>.json`은 NB CSM multiple 전용이므로 위 룰에 사용하지 않음. **parser 레인**(IR 정형 추출 활성화 시)이 분기별 IR factsheet에서 아래 schema로 추출해 채워야 활성화됨. ※ 옛 "gathering" 단계는 2026-05-31 publishing으로 머지된 죽은 stage 이므로 IR factsheet 정형 추출 주체 = parser.)

**Expected schema** (모든 값 **억원** 단위, missing 항목은 `null`):
```json
{
  "company": "삼성화재해상보험",
  "kr": "KR0008",
  "period": "FY2026_Q1",
  "source_file": "(KOR) SFMI 26.1Q_f.xlsx",
  "csm_waterfall": {
    "opening": 138245.0,
    "new_business": 9120.3,
    "interest": 1820.4,
    "assumption": -540.1,
    "amortization": -7950.2,
    "closing": 140695.4
  },
  "csm_breakdown": {
    "보장성": 120300.0,
    "물보험": 8500.0,
    "저축성": 11895.4,
    "total": 140695.4
  },
  "segment_insurance_income": {
    "장기": 4320.5,
    "자동차": 980.1,
    "일반": 1250.7,
    "total": 6551.3
  },
  "notes": "..."
}
```

`segment_insurance_income` 블록은 **DEPRECATED** (2026-06-01) — §1.2 `SEGMENT_INSURANCE_INCOME_DART_VS_IR` 폐기와 함께 사용 안 함. 부문별 손익 정합성은 §1.5 `PL_BRIDGE_DART_INTERNAL`(DART 자기완결)로 대체. schema에 남겨두되 검증에 쓰지 않음.

**SKIP 매트릭스 (graceful degradation):**

| 상태 | 동작 |
|---|---|
| `data/ir/<period>/parsed/<KR>.json` 부재 | cross-source 룰(현재 `CSM_WATERFALL_DART_VS_IR`, `CSM_BREAKDOWN_DART_VS_IR`) SKIP (회사 단위) |
| `csm_waterfall.{step}` 값이 `null` | 해당 step만 SKIP, 나머지 step 계속 비교 |
| `csm_breakdown`에 segment 키가 없고 `total`만 있음 | segment 비교 SKIP, total만 비교 |
| `segment_insurance_income` | **무시** (DEPRECATED — §1.5로 대체) |
| IR 단위가 백만원 또는 천원 | parser 책임 — JSON에 들어올 때 이미 억원 변환 완료 가정. mismatch 발견시 parser RED. |

**알려진 IR 미공시 회사** (전체 SKIP — [source-catalog.yaml](source-catalog.yaml) `ir.known_gaps` 동기화):
- 교보생명, KDB생명, ABL생명, 흥국화재, 라이나, BNP, iM라이프, 메트라이프, 처브, AIA, 카카오페이손해, DB금융네트워크, 하나금융지주(보험분해 없음)

---

## 1.5 `PL_BRIDGE_DART_INTERNAL` — DART 자기완결 P&L bridge 정합성

**단일 소스(DART) 내부 정합성 룰. cross-source 아님 — IR factsheet 불필요.** 부문별 IFRS17 보험손익 주석을 쌓아 연결 포괄손익계산서 당기순이익까지 닫히는지 검증한다. 부문 주석 추출이 틀리면 bridge가 안 닫혀서 RED로 잡힌다. (소유자: 삼성화재 2025.4Q 수기 모델 `보험손익 breakdown.xlsx`에서 도출, 검증 셀 전부 True.)

**왜 이게 SEGMENT cross-source를 대체하나:** IR 부문별 손익 = DART 부문 서비스손익 + (IR 고유 키로 배분한 기타영업수익/기타사업비용). DART는 기타항목을 전사 단일값으로만 공시 → IR 정의 재현 불가. 그러나 **전사 레벨에서는** `Σ부문 서비스손익 + 전사 기타영업수익 − 전사 기타사업비용 = 전사 보험손익`이 항등식으로 성립하므로, 부문 추출 정확성을 P&L 총계로 검증할 수 있다.

**입력 (둘 다 DART 추출):**
1. **연결 포괄손익계산서** 항목값: `보험손익 / 보험영업수익 / 보험수익 / 재보험수익 / 기타영업수익 / 보험영업비용 / 보험서비스비용 / 재보험비용 / 기타사업비용 / 투자손익 / 영업이익 / 영업외수익 / 영업외비용 / 법인세차감전순이익 / 법인세비용 / 당기순이익`
2. **부문별 IFRS17 보험손익 주석**: 부문(손보 `장기/자동차/일반`) × {보험수익 행들, 보험서비스비용 행들, 재보험비용 행들, 재보험수익 행들}

**부문 서비스손익 도출** (항목명 기반, 행번호는 회사별 상이):
```
부문손익[seg] = Σ(보험수익 행[seg]) + Σ(재보험수익 행[seg]) − Σ(보험서비스비용+재보험비용 행[seg])
```

**검증 등식** (전부 만족해야 PASS — 하나라도 초과 시 RED):

| id | 등식 | 의미 |
|---|---|---|
| B1 | `보험수익(P&L) = Σ_seg(부문주석 보험수익)` | 부문 보험수익 추출 정확성 |
| B2 | `재보험수익(P&L) = Σ_seg(부문주석 재보험수익)` | 부문 재보험수익 추출 정확성 |
| B3 | `보험서비스비용(P&L) = Σ_seg(부문주석 보험서비스비용)` | 부문 비용 추출 정확성 |
| B4 | `재보험비용(P&L) = Σ_seg(부문주석 재보험비용)` | 부문 재보험비용 추출 정확성 |
| B5 | `보험영업수익 = 보험수익 + 재보험수익 + 기타영업수익` | P&L 소계 정합 |
| B6 | `보험영업비용 = 보험서비스비용 + 재보험비용 + 기타사업비용` | P&L 소계 정합 |
| B7 | `보험손익 = 보험영업수익 − 보험영업비용` | = `Σ부문손익 + 기타영업수익 − 기타사업비용` |
| B8 | `영업이익 = 보험손익 + 투자손익` | |
| B9 | `법인세차감전순이익 = 영업이익 + 영업외수익 − 영업외비용` | |
| B10 | `당기순이익 = 법인세차감전순이익 − 법인세비용` | |

**Tolerance:** per-등식 `max(0.1%·|expected|, 200mn KRW)`. (원본 수기 모델은 `ROUND(,0)` 일치 / `ABS<2백만` 수준이지만, 파이프라인 추출 반올림 노이즈 floor로 200mn 부여.)

**Severity:** RED → parser loopback. `suspected_source`: B1–B4 실패는 `"DART"` (부문 주석 추출), B5–B10 실패는 `"internal"` (P&L 항목 추출/매핑).

**삼성화재 2025.4Q 검증례** (백만원, 전부 PASS):
- B7 보험손익: `1,672,913 (부문합) + 16,728 (기타영업수익) − 206,607 (기타사업비용) = 1,483,034` = P&L 보험손익 ✓
- B8 영업이익: `1,483,034 + 1,176,109 = 2,659,143` ✓
- B9 세전: `2,659,143 + 124,167 = 2,783,309` ✓
- B10 당기순이익: `2,783,309 − 763,023 = 2,020,287` ✓

**일반화 주의:** 부문 주석/포괄손익계산서 **행 순서·항목 수는 회사별로 다름** (V7 `csm_leaf_cols` layout 문제와 동형). 항목명 기반 매핑 필수, 행번호 하드코딩 금지. 현재 삼성화재 1사만 수기 검증됨 — 다른 손보사 적용 전 행 매핑 확인 필요. **선행조건: parser가 부문별 보험손익 주석 + 연결 포괄손익계산서를 정형 추출해야 활성화** (현재 미추출 → 룰 SKIP 상태).

**🔬 진단 가이드 — 보험손익 등식 잔차의 진짜 원인 (2026-06-07 parser 제보)**: 보험손익 dual-form이 작은 잔차로 안 닫힐 때 **"기타영업수익 누락"으로 오진하지 말 것** (한화손보·삼성화재 2건 연속 오진). **별도(OFS) 기준 회사는 FS-API상 기타영업수익이 구조적으로 0** (`보험영업수익 = 보험수익 + 재보험수익`, 기타영업수익 별도 라인 없음). 따라서 보험손익 잔차의 진짜 원인은 대개 **ΣLOB의 별도/연결 레그 오선택**: parser의 component 노트 `pmin`("최소합계=별도") 휴리스틱이 **재보험 레그에서 뒤집힘**(연결이 그룹내부 재보험을 상계해 별도 재보험 > 연결). 그 결과 보험수익은 별도, 재보험회수는 연결로 **기준 불일치** → ΣLOB 결손/과대. **분기마다 별도/연결 대소가 달라 같은 회사도 일부 분기만 fail**(우연히 맞는 분기는 닫힘). → 보험손익 잔차는 **LOB 별도/연결 기준 일관성부터 의심**하고 parser에 LOB 레그 재확인 요청. 수정 패턴: 별도 보험수익(min 합계) anchor + cost/재보험 레그를 같은 문서 블록에서 `first_from`으로 선택(4레그 동일 기준).

**🚫 dual-form 정당성 — 과잉 진단 금지 (2026-06-07 철회, 다시 시도 말 것)**: 보험손익은 회사·분기에 따라 `ΣLOB`(**bare**) 또는 `ΣLOB + 기타영업수익 − 기타사업비용`(**adj**) 중 하나로 닫힌다 — 일부 회사·분기는 종목별 합산에 기타사업비가 이미 녹아 있어 bare로 닫힌다. **둘 중 하나만 닫혀도 PASS.** 특히 **bare-close는 정상이지 "숨은 LOB 결손/dual-form 허점"이 아니다 — flag 금지** (흥국 2024.4Q를 그렇게 오진했다 철회). **"회사별 form 고정 flag" 제안도 철회** (분기마다 form이 갈리므로 고정 불가). dual-form은 이 케이스를 통과시키려는 **의도된 설계**.

### 1.5.1 마스터테이블 입력 계약 (`PL_breakdown` / `CSM_waterfall` / `CSM_amortization`)

사용자가 회사별 수기 모델을 **long-format JSON 마스터테이블** 3종으로 정형화하여 관리. `PL_BRIDGE_DART_INTERNAL`·`CSM_CROSSCHECK_WATERFALL_VS_PL`·`CSM_WATERFALL_CLOSING_IDENTITY`의 입력.

**공통 long-format row 스키마** (`PL_breakdown`, `CSM_waterfall`):
```json
{ "원보험사코드": "KR0008", "원수사명": "삼성화재", "티커": "...",
  "생손보여부": "손해보험", "항목번호": 3, "항목명": "CSM상각",
  "공시분기": "2025.4Q", "값": 1620781 }   // 값 단위: 백만원
```

- **`PL_breakdown`** 항목명 셋: `보험손익 / 장기 손익 / CSM상각 / RA(위험조정변동) / 예실차 등 / 자동차손익 / 일반손익 / 기타영업수익 / 기타사업비용 / 투자손익 / 투자이익 / 보험금융손익 / 영업이익 / 영업외손익 / 세전이익 / 법인세 / 당기순이익`
- **`CSM_waterfall`** 항목명 셋: `기초 CSM / 신계약 CSM / 이자 부리 / 가정 및 경험 조정 / CSM 상각 / 기말 CSM`
- **`CSM_amortization`** (별도 스키마, 상각 스케줄): `{원보험사코드, 원수사명, 티커, 생손보여부, 공시분기, 경과차년, 상각액}`. 경과연차별 CSM 상각 예상 — 현재 cross-check에 미사용(미래 확장용).

**cross-check 매칭:** `(원보험사코드, 공시분기)`로 두 마스터 row 묶고, **항목명 공백 정규화** 후 비교. `CSM상각`(PL, 양수) ↔ `CSM 상각`(waterfall, 음수)은 정규화로 동일 항목 인식. `신계약 CSM`은 `CSM_waterfall`에만 존재 → PL 짝 없으면 SKIP.

**현재 상태:** `PL_breakdown` 삼성화재 2025.4Q만 값 채워짐, `CSM_waterfall`·`CSM_amortization`은 분기 행 템플릿만(값 None) → 데이터 채워지면 룰 자동 활성.

---

## 2. 신규 공통 룰: `QOQ_DELTA_WARN` (모든 도메인 적용)

직전 분기 대비 변동률이 비정상적으로 크면 경고. **anomaly detection이지 산술 정합성 검증이 아니므로 YELLOW** (RED 아님 → loopback 안 돌림).

### 2.1 임계값
- 기본: `|ΔQoQ| > 15%`
- 절대값 floor: `|prev| < 1억원`(K-ICS) / `|prev| < 100mn`(IFRS17) → SKIP (rounding noise)
- item별 override는 `config/qoq_thresholds.yaml`에 등록 (없으면 15% default)

### 2.2 비누적 항목 (대부분의 K-ICS 시점값)
```
delta = (current - prev) / |prev|
```
- `prev == 0` 이고 `current` 가 floor 이상이면 YELLOW
- 신규 항목(직전 분기 데이터 없음)은 SKIP

### 2.3 누적 항목 (FY 내 누적 → 다음 FY 1Q에 reset)
**예시:** IFRS17 `new_business_csm` (1Q→2Q→3Q→4Q 누적, 익년 1Q에 drop)

`net 분기 기준`으로 비교:
```
net_this_q = current - prev          (같은 FY 내)
net_prev_q = prev    - prev_prev     (같은 FY 내)
net_QoQ_delta = (net_this_q - net_prev_q) / |net_prev_q|
```

**FY rollover (직전=4Q, 현재=1Q):** reset이므로 `net_this_q = current` 자체. 작년 1Q의 `net`(=작년 1Q값)과 비교.

**누적 항목 등록 목록** (확장 시 본 섹션 갱신):
- IFRS17: `new_business_csm`, `csm_amortization`, `insurance_revenue` (다른 누적항목 등록 시 추가)
- K-ICS: (해당 없음 — 모두 시점값)
- Misc: (등록 시 추가)

### 2.4 출력 메시지 포맷
```
item={X} company={Y} quarter={Q} QoQ_delta={D%} exceeds 15% threshold (basis={raw|net_quarterly})
```

---

## 3. Loopback workflow (실패 시)

**원칙:** RED가 생기면 **직전 단계 parser 서브에이전트**에게 재확인을 요청한다. **최대 5회.**

### 3.0 전달 메커니즘 = inbox (사람 복붙 아님)

계약 정본: [`inbox/README.md`](../../inbox/README.md). §3의 parser loopback은 **inbox md로** 전달한다 — 사람이 세션 간 복붙하지 않는다.

- **내 inbox**: `inbox/validation/` — parser가 재작업 결과를 `status: answered`로 떨굼.
- **시작 시 첫 동작**: 내가 보냈던 `answered` 메시지 재확인 → 재검증 통과면 `status: resolved` + `_resolved/` 이동, 실패면 같은 스레드에 `iter++` 새 노트 (`iter==5`면 `route: escalate`로 바꿔 사람 큐).
- **route 분류 (mechanical=script, judgment=agent)**:
  - **기계적 raise**: validator JSON → `route: reparse` 메시지(`inbox/parser/`)는 스크립트 [`scripts/consolidate_inbox.py`](../../scripts/consolidate_inbox.py)가 한다. idempotent(기존/`_resolved/` 중복 skip). 손으로 쓰지 말 것. 루프: validator 실행 → `consolidate_inbox.py` → "inbox 확인해라".
  - **판단 라우팅(에이전트 몫)**: parser 진단 회신 후 reparse를 재분류 — 원천 애매(별도-연결 무앵커)/앙상블 불일치/iter 5회 초과 → `route: escalate`(사람 큐); 룰로 못 잡는 비-IR 균일오류 → `route: blind_spot`(사람·2nd소스); raw 의심(파싱불가 시그니처) → `route: refetch`(`inbox/downloader/`).
- 흩어진 검증 JSON(`csm_continuity_validation` / `nb_csm_validation` / `csm_waterfall_validation` 등)은 **근거**로 그대로 둔다. 신규 validator를 inbox에 흘리려면 `consolidate_inbox.py`의 `VALIDATORS`에 핸들러 추가 (waterfall must_reparse는 버킷 비면 미적용 — 항목 생기면 추가).
- **참고 검증기**: closing-identity가 못 보는 off-year/basis-swap은 [`scripts/validate_csm_continuity.py`](../../scripts/validate_csm_continuity.py) (within-FY 기초 일정 + FY경계 기말→기초 연속성, RED) — mutation-test(`scripts/_probes/_mutation_test_csm.py`)가 사각지대로 식별해 추가됨.
- 에이전트는 inbox를 자동 감시하지 않음 — 드라이버(Workflow/사람)가 호출 시 드레인.
- **⚠️ 빌드 체인 gotcha (재검증 전 필수 확인)**: parser가 소스(`csm_waterfall_master_diag.json` / viz JSON)를 고쳐도 **`python scripts/build_root_masters.py` 재실행 전엔 검증 대상 루트 마스터(`CSM_waterfall.json` 등)에 반영 안 됨.** parser `answered` 재확인 시 **소스 mtime > 루트 mtime이면 빌드 누락** — "고쳤는데 검증값 그대로"의 정체. 빌드 돌리고(또는 parser/publishing에 요청) 재검증. (2026-06-07 흥국 3회 재검증 헛돈 원인.)

아래 §3.1은 위 메커니즘 위에서 도는 검증 retry 루프의 의미.

```
LOOP (max 5 iterations):
  1. Validate → RED 있음
  2. RED를 packaging:
       { rule_id, item, company, quarter, expected, actual,
         raw_source_path (MD/XML/PDF), suspected_cause,
         suspected_source: "DART" | "IR" | "internal" }
     - §1.2의 DART↔IR 교차검증 3개 룰은 항상 `suspected_source: "DART"` (IR을 ground truth로 가정).
       만약 운영자가 IR이 의심된다고 사전 표기한 케이스라면 escalate_to_human으로 분기.
  3. parser에 reparse 발주 — **전달은 §3.0 inbox md(`inbox/parser/` 메시지)가 정본.**
     (Agent tool로 parser subagent를 직접 invoke하던 옛 모델은 gathering-era 잔재 = 폐기. 아래는 *메시지 내용*의 의미일 뿐, 실제 전달 채널은 inbox.)
       - 대상 lane/도메인 명시: `lane: kics|ifrs17` + 도메인 ref(docs/domains/claude-agent-{kics,ifrs17}.md)
       - 메시지: "재파싱 요청 — 다음 항목의 raw source(suspected_source 기준)를
                  다시 확인하고 대상 JSON의 해당 row를 갱신해달라.
                  변경사항을 1줄 요약으로 회신."
       - packaging된 RED 묶음(suspected_source 포함)을 그대로 inbox 메시지 본문에 전달
       - DART↔IR 교차검증 RED는 DART 본문 XML/주석 재스킴이 default action
  4. Parser 반환 후 갱신된 JSON으로 재검증 → loop_iteration++
  5. RED=0 또는 loop_iteration==5 도달 시 종료
```

### 종료 분기
| 조건 | next_action | exit | 후속 |
|---|---|---|---|
| RED=0 | `pass` | 0 | 다운스트림 진행 |
| YELLOW만 있고 RED=0 | `pass` | 0 | YELLOW는 loop 안 돌림, 보고서에만 기록 |
| loop_iteration==5에도 RED>0 | `escalate_to_human` | 2 | [TODO.md](../../TODO.md)에 `(도메인, 회사코드, 분기, rule_id, "재파싱 5회 실패")` 한 줄 추가 + 메인 세션 보고 |

**기존 코드 영향:** [run_ifrs17_csm_reconcile_loop.py](../../scripts/run_ifrs17_csm_reconcile_loop.py)의 max-iter는 본 룰에 맞춰 **8 → 5로 갱신** (코드 변경은 별도 작업으로 발행).

---

## 4. Documented exception 처리

검증 실패가 알려진 데이터 한계(OCR 회사, IR 미공시, post-transition 데이터 부재 등)일 경우:

1. [TODO.md](../../TODO.md)에 해당 `(도메인, 회사코드, 분기, rule_id, 사유)` 라인이 이미 있는지 확인
2. 있으면 finding의 severity를 `SKIP`으로 다운그레이드, summary에서 제외
3. 없으면 일반 RED로 취급하여 retry loop 진입

**exception 추가는 사용자(운영자) 권한.** 서브에이전트가 자체 판단으로 TODO.md에 RED waiver를 쓰지 말 것. `escalate_to_human` 단계에서만 "재파싱 5회 실패" 사유로 기록.

---

## 5. 게이트 동작 (Downstream blocking)

| 도메인 | RED>0일 때 차단되는 것 | 차단되지 않는 것 |
|---|---|---|
| K-ICS | JSON swap, template sync, K-ICS.html 리빌드, git push | — (전부 차단) |
| IFRS17 | `templates/data/assoc/` JSON sync | **HTML deploy 자체는 차단 X** (panel-level "data missing" stub 허용) |
| Misc IR | K-ICS 룰 RED와 동일 처리 (전부 차단) | — |

YELLOW(QoQ warn 포함)는 어떤 다운스트림도 차단하지 않는다. 보고서에 기록되고, 운영자가 사후 검토.

---

## 6. 호출 예시 (메인 세션 → validation 서브에이전트)

```javascript
Agent({
  subagent_type: "general-purpose",
  description: "K-ICS validation + retry loop",
  prompt: `
본 문서를 작업 지시서로 따른다: docs/agents/claude-agent-validation.md

domain: kics
target: kics_disclosure.json
prior_snapshot: snapshots/kics_2026Q1.json
parser_agent_doc: docs/agents/claude-agent-parser.md  # 도메인 ref: docs/domains/claude-agent-kics.md

루프 결과를 artifacts/validation/kics_<ts>.json에 저장하고,
next_action 과 summary를 회신할 것.
`
})
```

병렬 도메인 검증이 필요할 땐 한 메시지에서 도메인 수만큼 Agent를 동시에 띄운다 (CLAUDE.md "멀티에이전트 병렬처리 규칙").

---

## 7. 변경 이력
- 2026-06-01 (c): 통합 마스터테이블 3종(`PL_breakdown` / `CSM_waterfall` / `CSM_amortization`, long-format) 입력 계약 §1.5.1 신설. `CSM_AMORT_WATERFALL_VS_PL` → **`CSM_CROSSCHECK_WATERFALL_VS_PL`** 확장: 항목명 공백 정규화(`"CSM상각"`=`"CSM 상각"`) 후 (1) CSM상각 부호반대 동규모, (2) 신계약 CSM 동값 일치(PL에 없으면 graceful SKIP — 신계약 CSM은 V7 IR 검증). 데이터 확인: 신계약 CSM은 `CSM_waterfall`에만, `PL_breakdown`엔 구조상 없음.
- 2026-06-01 (b): 메리츠 `CSM waterfall_메리츠.xlsx` 분석 → (1) `CSM_BREAKDOWN_DART_VS_IR`에 "측정요소별(전환방법별) 표만 내는 손보(메리츠)는 보종 분해 DART 부재 → 보종 비교 영구 SKIP" 명시. (2) CSM상각 cross-table 신설(이후 (c)에서 CSM_CROSSCHECK로 확장). 메리츠 CSM waterfall 출처 = "(4) 측정요소별 변동내역" 배당있는+없는 두 블록 합, CSM=D/E/F(수정소급/공정가치/그외) 3칼럼, 가정조정=잔차, closing identity 확인.
- 2026-06-01: `SEGMENT_INSURANCE_INCOME_DART_VS_IR` **폐기** — 부문별 손익 DART↔IR 비교 불가 (IR은 기타영업수익/사업비를 부문 배분, DART는 전사 단일값만 공시 → 재현 불가). 대체로 **§1.5 `PL_BRIDGE_DART_INTERNAL`** 신설 (DART 자기완결 P&L bridge: 부문 IFRS17 주석 → 포괄손익계산서 당기순이익까지 10개 등식 정합. 삼성화재 2025.4Q `보험손익 breakdown.xlsx`에서 도출, 검증 전부 True). §1.4 `segment_insurance_income` 입력 DEPRECATED 표기. 선행조건: parser 부문 주석 + 포괄손익계산서 정형 추출.
- 2026-05-31 (b): `NB_CSM_DART_VS_IR_ANNUAL_SUM` 정식 codify. Cohort 7사 고정 (IR series 보유 cohort, 확장 없음 — 21사는 IR factsheet 부재로 비교 불가). `data/ir/series/<KR>.json` quarterly nb_csm_eok annual sum을 ground truth로 사용. Tool: `scripts/check_nb_csm_widespread.py`. Severity RED. Gate enforcement는 publishing stage에서 집행. F18 활성화 후 `CSM_WATERFALL_DART_VS_IR` new_business step과 overlap → V7 retire 검토. `NB_CSM_MULTIPLE_RECONCILIATION`은 period-aware denominator + `fallback_used` 플래그 보강 (validation 정직성).
- 2026-05-31: DART↔IR 교차검증 3개 룰 추가 — `CSM_WATERFALL_DART_VS_IR` (step별, tol=max(5%, 100억)), `SEGMENT_INSURANCE_INCOME_DART_VS_IR` (손보 장기/자동차/일반, tol=max(10%, 50억); 생보 SKIP), `CSM_BREAKDOWN_DART_VS_IR` (손보 보장성/물보험/저축성 or total, tol=max(5%, 100억)). 전부 RED → DART parser loopback. §1.4 IR-side input 계약 신설 (`data/ir/<period>/parsed/<KR>.json`). RED packaging에 `suspected_source` 필드 추가.
- 2026-05-30: 초안 작성. R1–R10, IFRS17 CSM 룰셋 codify. 공통 `QOQ_DELTA_WARN` 룰 추가 (threshold=15%, 누적 항목은 net 분기 기준). retry loop max=5 (IFRS17 reconcile 8→5).
