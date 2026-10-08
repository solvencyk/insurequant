# Agent: Validation (파싱 숫자 정합성 + QoQ anomaly)

당신은 insurequant 데이터셋(K-ICS / IFRS17 / 기타 IR)에서 **파싱된 숫자의 정합성**을 검증하는 전담 서브에이전트다. 본 문서는 작업 지시서이며, 호출자(메인 세션)는 이 문서 경로를 컨텍스트로 넘긴다.

---

## 0. 작업 계약 (Contract)

**입력**
- `domain`: `kics` | `ifrs17` | `misc`
- `target`: 검증 대상 JSON 경로 (또는 디렉토리)
- `prior_snapshot`: 직전 분기 스냅샷 경로 (QoQ 비교용; 없으면 QoQ 룰 SKIP)
- `parser_agent_doc`: 실패 시 호출할 parser 서브에이전트의 가이드 문서 경로 (e.g. [claude-agent-parser.md](claude-agent-parser.md) / 도메인 reference는 [../domains/claude-agent-kics.md](../domains/claude-agent-kics.md))

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

> **룰 로직을 고치면 골든 필수.** `run_validation` 은 `_validate_bucket`(자본 1-3·요구자본 4-8) · `_validate_market_irr`(19_market·36_irr) ·
> `_validate_transition_basic`(8_post·8_life) · `_validate_transition_capital`(9·10)으로 나뉘어 있다. 고친 뒤
> **`python -m pytest tests/test_kics_rules_golden.py`**(라이브 마스터 findings 의 `(회사,분기,룰,상태)` 매트릭스, <1초).
> 마스터테이블 게이트(`validate_master_tables.py` 의 `_check_*` 7개)는 **`tests/test_master_tables_golden.py`**.
> 결과가 **의도적으로** 바뀌면 손으로 해시를 고치지 말고 `--update` 재생성 + 커밋 메시지에 **왜**.

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

> `36_irr` 는 `max(base−steep, 0)` 절단 때문에 41~46 중 한 칸이 크게 틀려도 못 볼 수 있다(2026-10-06 AIA 항목46 100배 — 듀레이션갭 역검산만 잡았다).

**K-ICS 금리민감도** (별도 마스터 `kics_rate_sensitivity.json`, 러너 `scripts/validate_kics_rate_sensitivity.py`. 정본: [`kics-rate-sensitivity-spec.md`](kics-rate-sensitivity-spec.md) §5):

| Rule | 검증 내용 | Tolerance / Severity |
|---|---|---|
| RS1_RATIO_IDENTITY | 각 (사,분기,경과조치)·각 충격컬럼: `비율 ≈ 지급여력금액/지급여력기준금액×100` | `max(0.5%p, 0.5%·\|비율\|)` / **RED→reparse** |
| RS2_BASE_ANCHOR | base vs `kics_disclosure` item1(금액)/item14(기준금액)/item27(비율) — **적용전↔`값` · 적용후↔`값_적용후` 둘 다** | 금액 2억 / 비율 0.5%p / **RED→reparse**. 예외 `RS2_EXCEPTIONS`(두 phase 공통): KR0011 2025.2Q(별도/연결 basis) · KR0009 2026.2Q(표간 불일치) |
| RS3_DIRECTION_SANITY | 생보 금리하락→비율하락 통상, 역방향 flag | — / YELLOW |
| RS4_COVERAGE_CENSUS | 회사 cadence(반기/분기) 인식 후 regime 내 hole | — / YELLOW |
| RS5_DISCLOSURE_COVERAGE | `kics_disclosure` 코호트의 (회사,분기)가 금리민감도 마스터에 **통째로** 없음(regime 2024.4Q+ 짝수분기) | — / **RED**. 선행 결손 17 = `RS5_EXCEPTIONS` |
| RS6_PHASE_LEVEL_CENSUS | 버킷 **안** 기대 그리드: 적용전·적용후 × 3 measure × 충격 5칸 (`ROW_MISSING·NULL_CELLS·UNKNOWN_LABEL·ORPHAN`) | — / **RED**. 선행 구멍 11키·31행 = `RS6_KNOWN_HOLES`(routed, `inbox/parser/20260921T1400Z`), inert 시 매니페스트 테스트가 해제 강제 |

### 1.2 IFRS17
- 러너: [validate_csm_waterfall.py](../../scripts/validate_csm_waterfall.py), [validate_nb_csm_multiple.py](../../scripts/validate_nb_csm_multiple.py)
- DART↔IR 교차검증 룰(굵게)은 IR 정형 파싱 보류로 **전사 SKIP** 이다. 입력 계약은 [ir-crosscheck-contract.md](ir-crosscheck-contract.md).

| Rule | 검증 내용 | Tolerance / Severity |
|---|---|---|
| CSM_WATERFALL_NEW_BUSINESS | new_business CSM 존재 + non-zero (IFRS17 §92) | — / RED |
| CSM_WATERFALL_CLOSING_IDENTITY | `opening + new_business + interest + assumption + amortization ≈ closing` | `max(500mn, 0.5%·|closing|)` / RED |
| **MASTER_COVERAGE** | (데이터 누락 hole — **SKIP으로 숨기지 않음**). closing/pl_bridge/crosscheck는 항목이 None이면 그 검사를 SKIP하므로, 거대한 skip 숫자 뒤에 "있어야 하는데 없는" 데이터가 숨음. 별도 census: **active 회사**(핵심항목 ≥7분기 보유)의 빈 분기 = hole. **2024+ = real hole(채워야)**, 2023 = known(사이트 비노출), <7분기 = structural(외국계·소형 미공시, 제외). 도구 `validate_master_tables.py` 0번. | real hole → **RED(데이터 채움 요청)** |
| **CSM_WATERFALL_PLAUSIBILITY** | (절댓값 sanity — closing identity 사각지대 보강). closing은 **내부 산술 합산만** 봐서 (a)분기 복붙 (b)기말 폭락 (c)기초≠전년말을 통과시킴(가정조정이 잔차 흡수). 3종 검사: **복붙(dup)** = 같은 회사 다른 분기 기말 CSM 동일, **폭변(spike)** = 기말 `\|ΔQoQ\|>50%`, **연속성(cont)** = `FY[t] 각 분기 기초 = FY[t-1].4Q 기말`(tol max(0.5%, 2억); 2023 SKIP). 도구 `scripts/validate_master_tables.py` 1b. | dup/배수·큰Δ → **RED(재추출)**, spike·작은Δ → YELLOW(재작성 검토) |
| MINIMUM_STAGE_COVERAGE | opening/new_business/closing 셋 다 non-null | — / RED |
| NB_CSM_MULTIPLE_RECONCILIATION | IFRS17 NB CSM ÷ KIDI 월납환산 vs IR 공시 multiple (6가지 변환 중 1개 통과면 PASS). period-aware denominator + `fallback_used` 플래그(meta `cohort_fallback_pass`)로 aligned-period 실패 후 tolerance 우연 통과를 드러낸다 | rel=0.25 OR abs=3.0 / **YELLOW** (loopback 없음) |
| **NB_CSM_DART_VS_IR_ANNUAL_SUM** | DART `csm_waterfall.json` `new_business.value_mn_krw` (FY annual) vs `data/ir/series/<KR>_<name>.json` 에서 convention-aware 로 derive 한 IR FY total(① 모든 분기 `nb_csm_singleQ_eok` 합 ② `metric` 에 `YTD`/`누계`/`cumulative` 면 Q4 값 ③ 그 외 분기 `nb_csm_eok` 합). Cohort = IR series 보유 7사. 도구 **미구현**(`check_nb_csm_widespread.py` 는 존재한 적 없다; 가장 가까운 것은 `scripts/check_nb_csm_history.py`). | `max(0.05·|IR|, 100억원)` per company / **RED → DART parser loopback** |
| **CSM_WATERFALL_DART_VS_IR** | DART CSM waterfall **step별** 값 vs IR factsheet 동일 step(`opening / new_business / interest / assumption / amortization / closing`). IR 이 공시한 step 만 비교. | `max(0.05·|IR_value|, 100억원)` per step / **RED → DART parser loopback** |
| **CSM_BREAKDOWN_DART_VS_IR** | CSM 잔액 분해 비교. 손보는 IR 이 `보장성 / 물보험 / 저축성` 을 주면 구분별, 아니면 `total`. 생보는 `total`. DART 가 보종 분해를 안 내는 회사(메리츠 — 측정요소별 표만)는 보종 비교 영구 SKIP. | `max(0.05·|IR_value|, 100억원)` per item / **RED → DART parser loopback** |
| **PL_BRIDGE_DART_INTERNAL** | DART 단일 소스 내부 P&L bridge 정합성 (cross-source 아님). 상세 등식·tolerance·입력은 **§1.5**. | per-등식 `max(0.1%·|expected|, 200mn)` / **RED → DART parser loopback** |
| **CSM_CROSSCHECK_WATERFALL_VS_PL** | 같은 (회사코드, 분기)의 `PL_breakdown` ↔ `CSM_waterfall` 에서 **항목명 정규화**(공백 무시) 후 공통 CSM 항목 일치 검증. **(1) CSM상각**: `PL.(원수+수재)CSM상각`(양수, 백만원) + `waterfall.CSM상각`(음수, 억원 ×100) ≈ 0. 재보험사(코리안리)는 PL 쪽 `원수 + 수재` 합산, 출재(9-1)는 제외. **4Q-only**(둘 다 YTD 누적). **(2) 신계약 CSM**: `PL_breakdown` 에는 구조상 없으므로 SKIP(V7 IR 검증 + closing identity 가 담당). | **3단계**: OK ≤ `max(5%·\|pl\|, 300mn)` / MINOR ≤ 10% (경고, pass) / **RED > 10% → parser loopback** |

### 1.3 Misc IR / 정기경영공시
- **misc는 별도 lane이 아니라 보조 도메인**(K-ICS 룰 R1–R10을 재사용하는 부수 항목; 병렬 레인은 kics·ifrs17 둘뿐).
- 정형 validator 없음. **K-ICS 룰 R1–R10을 그대로 재사용**.
- 추가: [quality_check.py](../../src/solvency/parser/quality_check.py) `score() < 0.7` 또는 critical row 누락 → YELLOW + review_queue CSV 생성.

### 1.4 IR 교차검증 데이터 계약

휴면 — [ir-crosscheck-contract.md](ir-crosscheck-contract.md)(IR-side 입력 경로·schema·SKIP 매트릭스·IR 미공시 회사 목록).

---

## 1.5 `PL_BRIDGE_DART_INTERNAL` — DART 자기완결 P&L bridge 정합성

**단일 소스(DART) 내부 정합성 룰. cross-source 아님 — IR factsheet 불필요.** 부문별 IFRS17 보험손익 주석을 쌓아 연결 포괄손익계산서 당기순이익까지 닫히는지 검증한다. 부문 주석 추출이 틀리면 bridge가 안 닫혀서 RED로 잡힌다.

**왜 SEGMENT cross-source 를 대체하나:** IR 부문별 손익 = DART 부문 서비스손익 + (IR 고유 키로 배분한 기타영업수익/기타사업비용). DART는 기타항목을 전사 단일값으로만 공시 → IR 정의 재현 불가. 그러나 **전사 레벨에서는** `Σ부문 서비스손익 + 전사 기타영업수익 − 전사 기타사업비용 = 전사 보험손익`이 항등식으로 성립하므로, 부문 추출 정확성을 P&L 총계로 검증할 수 있다.

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

**Tolerance:** per-등식 `max(0.1%·|expected|, 200mn KRW)`.

**Severity:** RED → parser loopback. `suspected_source`: B1–B4 실패는 `"DART"` (부문 주석 추출), B5–B10 실패는 `"internal"` (P&L 항목 추출/매핑).

**일반화 주의:** 부문 주석/포괄손익계산서 **행 순서·항목 수는 회사별로 다름**. 항목명 기반 매핑 필수, 행번호 하드코딩 금지.

**🔬 진단 — 보험손익 등식 잔차의 진짜 원인**: dual-form 이 작은 잔차로 안 닫힐 때 **"기타영업수익 누락"으로 오진하지 말 것**(한화손보·삼성화재 2건 연속 오진). **별도(OFS) 기준 회사는 FS-API상 기타영업수익이 구조적으로 0** 이다. 잔차의 진짜 원인은 대개 **ΣLOB의 별도/연결 레그 오선택** — component 노트 `pmin`("최소합계=별도") 휴리스틱이 **재보험 레그에서 뒤집힌다**(연결이 그룹내부 재보험을 상계해 별도 재보험 > 연결). 분기마다 별도/연결 대소가 달라 같은 회사도 일부 분기만 fail 한다. → **LOB 별도/연결 기준 일관성부터 의심**하고 parser에 LOB 레그 재확인 요청. 수정 패턴: 별도 보험수익(min 합계) anchor + cost/재보험 레그를 같은 문서 블록에서 `first_from`으로 선택(4레그 동일 기준).

**🚫 dual-form 정당성 — 과잉 진단 금지**: 보험손익은 회사·분기에 따라 `ΣLOB`(**bare**) 또는 `ΣLOB + 기타영업수익 − 기타사업비용`(**adj**) 중 하나로 닫힌다. **둘 중 하나만 닫혀도 PASS.** bare-close 는 정상이지 "숨은 LOB 결손"이 아니다 — flag 금지. "회사별 form 고정" 도 불가(분기마다 갈린다).

**🔴 등식이 닫히는 것과 값이 맞는 것은 다르다 — PL 9식 중 5식은 구성상 참이다.**
빌더(`build_pl_breakdown.assemble` · `fetch_dart_fs._parse`)가 우변의 한 항을 좌변에서 빼서
만들기 때문에(`item7 = 3−(4+5+6)` · `item12 = 8−(9+10+11)` · `item18 = 17−19` ·
`item21 = 22−20` · `item23 = 22−24`) 그 등식들은 **산수상 깨질 수가 없다.** 게이트 SUMMARY 는
`pl_bridge:…P(진짜…·구성상…·부분…)` 로 인쇄한다 — **`구성상` 쪽 숫자를 근거로 "검사했더니 깨끗" 이라고 쓰지 마라.**

- 판정은 `validate_master_tables.PL_EQ_EVIDENCE`(등식별 `REAL`/`TAUTOLOGY`/`PARTIAL`)에 있고, 무검사 항목 목록은 `PL_ITEMS_UNCHECKABLE_BY_EQUATION` 이 매 실행 인쇄한다.
- **item5·6·9·10·11·19·23 은 등식으로 영원히 못 본다** — 원문 재대조만이 수단이다. 특히 **item6(예실차)** 은 독립 앵커(원문 표의 보험수익·소계 재판독)로만 검증된다.
- item22 는 게이트 2f `TAX22_SOURCE_CROSSCHECK`(`|22−24| == |원천 법인세 계정|`, FS-API 캐시)가 본다. 그 룰이 안 보는 버킷은 게이트가 사유별로 세어 인쇄한다.
- `tests/test_rule_coverage_manifest.py::PL_CONSTRUCTIVE_BLIND` / `PL_CONSTRUCTIVE_GUARDED` 가 이것을 변이시험으로 매 push 강제한다.
- **`tests/test_identity_tautology.py` 를 PL 에 그대로 배선하지 마라.** 그 귀무모형은 등식 단위 반올림을 가정하는데 PL 마스터는 원÷1e6 이라 건전한 항등식도 잔차가 정확히 0 이다.

### 1.5.1 마스터테이블 입력 계약 (`PL_breakdown` / `CSM_waterfall` / `CSM_amortization`)

long-format JSON 마스터 3종. `PL_BRIDGE_DART_INTERNAL`·`CSM_CROSSCHECK_WATERFALL_VS_PL`·`CSM_WATERFALL_CLOSING_IDENTITY`의 입력.

**공통 long-format row 스키마** (`PL_breakdown`, `CSM_waterfall`):
```json
{ "원보험사코드": "KR0008", "원수사명": "삼성화재", "티커": "...",
  "생손보여부": "손해보험", "항목번호": 3, "항목명": "CSM상각",
  "공시분기": "2025.4Q", "값": 1620781 }   // 값 단위: 백만원
```

- **`PL_breakdown`** 항목명 셋: `보험손익 / 장기 손익 / CSM상각 / RA(위험조정변동) / 예실차 등 / 자동차손익 / 일반손익 / 기타영업수익 / 기타사업비용 / 투자손익 / 투자이익 / 보험금융손익 / 영업이익 / 영업외손익 / 세전이익 / 법인세 / 당기순이익`
- **`CSM_waterfall`** 항목명 셋: `기초 CSM / 신계약 CSM / 이자 부리 / 가정 및 경험 조정 / CSM 상각 / 기말 CSM`
- **`CSM_amortization`** (별도 스키마, 상각 스케줄): `{원보험사코드, 원수사명, 티커, 생손보여부, 공시분기, 경과차년, 상각액}`. 현재 cross-check에 미사용.

**cross-check 매칭:** `(원보험사코드, 공시분기)`로 두 마스터 row 묶고, **항목명 공백 정규화** 후 비교. `신계약 CSM`은 `CSM_waterfall`에만 존재 → PL 짝 없으면 SKIP.

---

## 2. 공통 룰: `QOQ_DELTA_WARN` (모든 도메인 적용)

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
- IFRS17: `new_business_csm`, `csm_amortization`, `insurance_revenue`
- K-ICS: (해당 없음 — 모두 시점값)

### 2.4 출력 메시지 포맷
```
item={X} company={Y} quarter={Q} QoQ_delta={D%} exceeds 15% threshold (basis={raw|net_quarterly})
```

---

## 3. Loopback workflow (실패 시)

**원칙:** RED가 생기면 **직전 단계 parser 서브에이전트**에게 재확인을 요청한다. **최대 5회.**

### 3.0 전달 메커니즘 = inbox (사람 복붙 아님)

계약 정본: [`inbox/README.md`](../../inbox/README.md).

- **내 inbox**: `inbox/validation/` — parser가 재작업 결과를 `status: answered`로 떨군다.
- **시작 시 첫 동작**: 내가 보냈던 `answered` 메시지 재확인 → 재검증 통과면 `status: resolved` + `_resolved/` 이동, 실패면 같은 스레드에 `iter++` 새 노트 (`iter==5`면 `route: escalate`).
- **route 분류 (mechanical=script, judgment=agent)**:
  - **기계적 raise**: validator JSON → `route: reparse` 메시지는 [`scripts/consolidate_inbox.py`](../../scripts/consolidate_inbox.py)가 한다(idempotent). 손으로 쓰지 말 것. 루프: validator 실행 → `consolidate_inbox.py` → "inbox 확인해라". 신규 validator 는 `VALIDATORS` 에 핸들러 추가.
  - **판단 라우팅(에이전트 몫)**: 원천 애매(별도-연결 무앵커)/앙상블 불일치/iter 5회 초과 → `route: escalate`; 룰로 못 잡는 비-IR 균일오류 → `route: blind_spot`; raw 의심(파싱불가 시그니처) → `route: refetch`(`inbox/downloader/`).
- 흩어진 검증 JSON(`csm_continuity_validation` 등)은 **근거**로 그대로 둔다. closing-identity 가 못 보는 off-year/basis-swap 은 [`scripts/validate_csm_continuity.py`](../../scripts/validate_csm_continuity.py)가 본다.
- **⚠️ 빌드 체인 gotcha**: parser가 소스(`csm_waterfall_master_diag.json` / viz JSON)를 고쳐도 **`build_root_masters.py` 재실행 전엔 루트 마스터에 반영 안 됨.** `answered` 재확인 시 **소스 mtime > 루트 mtime이면 빌드 누락** — 빌드 돌리고(또는 parser/publishing에 요청) 재검증.

```
LOOP (max 5 iterations):
  1. Validate → RED 있음
  2. RED를 packaging:
       { rule_id, item, company, quarter, expected, actual,
         raw_source_path (MD/XML/PDF), suspected_cause,
         suspected_source: "DART" | "IR" | "internal" }
     - DART↔IR 교차검증 룰은 항상 `suspected_source: "DART"` (IR을 ground truth로 가정).
       운영자가 IR이 의심된다고 사전 표기한 케이스라면 escalate_to_human.
  3. parser에 reparse 발주 — 전달은 §3.0 inbox md(`inbox/parser/`, `lane: kics|ifrs17` + 도메인 ref).
     packaging된 RED 묶음을 그대로 본문에 싣고 "raw 재확인 후 해당 row 갱신, 1줄 요약 회신"을 요청.
  4. Parser 반환 후 갱신된 JSON으로 재검증 → loop_iteration++
  5. RED=0 또는 loop_iteration==5 도달 시 종료
```

### 3.1 가설 형성 방법론 (owner 2026-08-24)

**집계(aggregate) 패턴만 보고 `suspected_cause`를 단정해 발주문에 적지 말 것.** 최소 1건은
raw 나 전수 데이터로 그 가설을 반증 가능한 쿼리(20줄 안팎)를 직접 돌려본 뒤에만 원인으로
적는다. 못 돌렸으면 그 필드는 **관측(무엇이 다른가) + 질문(원문 어디에 어떻게 인쇄돼 있나)**
으로만 적어라. 서브에이전트에게 원인을 대신 정해 지시하지 말고, raw를 쥔 쪽이 직접 판정하게 한다
(이 규율 없이 가설 다섯 번이 다섯 번 다 틀린 기록 — `docs/changelog_validation.md` 2026-08-24).
룰 코드 수정으로 이어지는 가설은 **편집 전에 현행식·제안식을 같은 데이터에 나란히 걸어
닫힘/깨짐 양방향을 세는 전수 시뮬레이션**이 별도로 필요하다(1건 고치려다 129건 깨뜨릴 뻔했다).

### 종료 분기
| 조건 | next_action | exit | 후속 |
|---|---|---|---|
| RED=0 | `pass` | 0 | 다운스트림 진행 |
| YELLOW만 있고 RED=0 | `pass` | 0 | YELLOW는 loop 안 돌림, 보고서에만 기록 |
| loop_iteration==5에도 RED>0 | `escalate_to_human` | 2 | inbox `route: escalate` + 메인 세션 보고(사유 "재파싱 5회 실패") |

---

## 4. Documented exception 처리

검증 실패가 알려진 데이터 한계(OCR 회사, IR 미공시, post-transition 데이터 부재 등)일 경우:

1. 등재부 [`docs/kics_gate_exceptions.md`](../kics_gate_exceptions.md)와 코드 레지스트리에 해당 `(도메인, 회사코드, 분기, rule_id, 사유)` 가 이미 있는지 확인
2. 있으면 finding의 severity를 `SKIP`으로 다운그레이드, summary에서 제외
3. 없으면 일반 RED로 취급하여 retry loop 진입

**exception 추가는 사용자(운영자) 권한.** 서브에이전트가 자체 판단으로 RED waiver를 쓰지 말 것. 박제형 면제는 blanket skip 이 아니라 입력 셀·잔차를 매 실행 재검산하는 형태여야 한다(움직이면 RED 복귀, 근거 원장 `data/_gold/kics_exemption_provenance.json`).

---

## 5. 게이트 동작 (Downstream blocking)

| 도메인 | RED>0일 때 차단되는 것 | 차단되지 않는 것 |
|---|---|---|
| K-ICS | JSON swap, template sync, K-ICS.html 리빌드, git push | — (전부 차단) |
| IFRS17 | `templates/data/assoc/` JSON sync | **HTML deploy 자체는 차단 X** (panel-level "data missing" stub 허용) |
| Misc IR | K-ICS 룰 RED와 동일 처리 (전부 차단) | — |

YELLOW(QoQ warn 포함)는 어떤 다운스트림도 차단하지 않는다. 보고서에 기록되고, 운영자가 사후 검토.

### 5.1 사고 포스트모템 — 게이트 룰로 종결 (필수)

게이트가 놓친 사고(false-green·라이브 오표시·검증 사각)를 발견하면 **반드시 포스트모템으로 종결**한다.
정본: [`docs/postmortems/README.md`](../postmortems/README.md) · 템플릿:
[`_TEMPLATE.md`](../postmortems/_TEMPLATE.md) · 운영 스킬: `.claude/skills/incident-postmortem/`.

**종결 조건 5칸** (하나라도 비면 close 불가): ① 무엇이 통과했나(어떤 게이트가 왜 못 잡았나)
② 어떤 룰이었으면 잡았나(입력·판정식·임계값·severity·오탐억제) ③ 그 룰이 지금
배선됐나(함수+파일+scope+exit-code) ④ documented exception 근거·**등재 registry 위치**
⑤ 미배선 잔여 + 후속 티켓.

> **"배선했다"와 "강제된다"는 다르다** — ③ 확인 순서:
> ① `run_gate()` 나 `main()` 이 그 검사를 실제로 호출하나(주석 처리된 호출은 호출이 아니다)
> ② 그 결과가 exit code / `blocked` 에 들어가나(YELLOW 전용이면 안 막는다)
> ③ 훅(`.githooks/pre-push` + `core.hooksPath`)이 그 스크립트를 부르나.
> `tests/test_push_gate_wiring.py` 가 이 셋을 매니페스트로 강제한다 —
> `WIRED`/`NOT_A_PUSH_GATE`(파일 단위) + `DATA_CONTRACT_CHECKS`(`check_*` 단위).
> 검사를 빼거나 추가하면 **선언을 같이 고치지 않는 한 테스트가 막는다.**

### 5.2 데이터계약 게이트 규칙

- **게이트가 검사하는 파일 = 사용자가 보는 파일.** 새 아티팩트를 `validate_data_contract.py` `MASTER_FILES` 에 등록할 때 그 경로가
  **HTML 이 fetch 하는 경로와 같은지** 확인하라(배포 아티팩트는 저장소 루트의 `kics_tier{1,2}_utilization.json`·`kics_forward_capital.json` 등).
- **깨진 파일 ≠ 없는 파일.** optional 로더는 없으면 `None`, 존재하지만 파싱 불가면 `env.unreadable` 에 append 한다 —
  `check_artifact_readable` 이 그것을 `ARTIFACT_UNREADABLE` **RED** 로 올리며 `run_gate` 에서 가장 먼저 돈다. 새 로더도 같은 패턴을 지켜라.
- 룰 엔진은 `src/solvency/validation/kics_json_rules.py` 하나뿐이다.

---

## 6. 호출 예시 (메인 세션 → validation 서브에이전트)

```javascript
Agent({
  subagent_type: "validation",      // .claude/agents/validation.md (model: sonnet)
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

병렬 도메인 검증이 필요할 땐 한 메시지에서 도메인 수만큼 Agent를 동시에 띄운다(`CLAUDE.md` §10). 변경 이력은 `docs/changelog_validation.md`.
