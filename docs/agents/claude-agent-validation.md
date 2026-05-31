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

### 1.2 IFRS17
- 러너: [validate_csm_waterfall.py](../../scripts/validate_csm_waterfall.py), [validate_nb_csm_multiple.py](../../scripts/validate_nb_csm_multiple.py)
- DART↔IR 교차검증 룰(아래 굵게 표시)의 IR-side input 계약은 **§1.4** 참고. IR 정형 JSON이 없는 회사·항목은 자동 SKIP.

| Rule | 검증 내용 | Tolerance / Severity |
|---|---|---|
| CSM_WATERFALL_NEW_BUSINESS | new_business CSM 존재 + non-zero (IFRS17 §92) | — / RED |
| CSM_WATERFALL_CLOSING_IDENTITY | `opening + new_business + interest + assumption + amortization ≈ closing` | `max(500mn, 0.5%·|closing|)` / RED |
| MINIMUM_STAGE_COVERAGE | opening/new_business/closing 셋 다 non-null | — / RED |
| NB_CSM_MULTIPLE_RECONCILIATION | IFRS17 NB CSM ÷ KIDI 월납환산 vs IR 공시 multiple (6가지 변환 중 1개 통과면 PASS) | rel=0.25 OR abs=3.0 / **YELLOW** (loopback 없음) |
| **CSM_WATERFALL_DART_VS_IR** | DART CSM waterfall **step별** 값 vs IR factsheet 동일 step. 비교 step = `opening / new_business / interest / assumption / amortization / closing`. step 하나라도 임계 초과 → RED. IR이 일부 step만 공시 → 공시된 step만 비교, 나머지 SKIP. | `max(0.05·|IR_value|, 100억원)` per step / **RED → DART parser loopback** |
| **SEGMENT_INSURANCE_INCOME_DART_VS_IR** | 부문별 보험손익 비교. **손보:** `장기 / 자동차 / 일반` 3개 segment. **생보:** 스키마 확정 전까지 SKIP. segment 단위로 individual 비교, 합계도 cross-check. | `max(0.10·|IR_value|, 50억원)` per segment / **RED → DART parser loopback** |
| **CSM_BREAKDOWN_DART_VS_IR** | CSM 도해(잔액 분해) 비교. **손보:** IR이 `보장성 / 물보험 / 저축성` 구분을 제공하면 구분별 비교, 안 하면 `total`만 비교. **생보:** 현재는 `total`만 비교. | `max(0.05·|IR_value|, 100억원)` per item / **RED → DART parser loopback** |

### 1.3 Misc IR / 정기경영공시
- 정형 validator 없음. **K-ICS 룰 R1–R10을 그대로 재사용**.
- 추가: [quality_check.py](../../src/solvency/parser/quality_check.py) `score() < 0.7` 또는 critical row 누락 → YELLOW + review_queue CSV 생성.

### 1.4 IR 교차검증 데이터 계약 (DART ↔ IR cross-source)

§1.2의 굵은 3개 룰(`CSM_WATERFALL_DART_VS_IR`, `SEGMENT_INSURANCE_INCOME_DART_VS_IR`, `CSM_BREAKDOWN_DART_VS_IR`)은 IR-side 정형 JSON이 있어야 동작.

**IR-side input path:** `data/ir/<period>/parsed/<KR>.json`

(현재 `data/ir/series/<KR>_<name>.json`은 NB CSM multiple 전용이므로 위 룰에 사용하지 않음. parser/gathering 단계가 분기별 IR factsheet에서 아래 schema로 추출해 채워야 활성화됨.)

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

생보의 `segment_insurance_income` 키 셋은 추후 확정. 그때까지 생보 회사는 해당 룰 SKIP.

**SKIP 매트릭스 (graceful degradation):**

| 상태 | 동작 |
|---|---|
| `data/ir/<period>/parsed/<KR>.json` 부재 | 3개 룰 전체 SKIP (회사 단위) |
| `csm_waterfall.{step}` 값이 `null` | 해당 step만 SKIP, 나머지 step 계속 비교 |
| `csm_breakdown`에 segment 키가 없고 `total`만 있음 | segment 비교 SKIP, total만 비교 |
| 손보인데 `segment_insurance_income` 부재 | SEGMENT 룰 SKIP |
| 생보 + `segment_insurance_income` 부재 | SKIP (현재 기본값) |
| IR 단위가 백만원 또는 천원 | parser 책임 — JSON에 들어올 때 이미 억원 변환 완료 가정. mismatch 발견시 parser RED. |

**알려진 IR 미공시 회사** (전체 SKIP — [source-catalog.yaml](source-catalog.yaml) `ir.known_gaps` 동기화):
- 교보생명, KDB생명, ABL생명, 흥국화재, 라이나, BNP, iM라이프, 메트라이프, 처브, AIA, 카카오페이손해, DB금융네트워크, 하나금융지주(보험분해 없음)

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

```
LOOP (max 5 iterations):
  1. Validate → RED 있음
  2. RED를 packaging:
       { rule_id, item, company, quarter, expected, actual,
         raw_source_path (MD/XML/PDF), suspected_cause,
         suspected_source: "DART" | "IR" | "internal" }
     - §1.2의 DART↔IR 교차검증 3개 룰은 항상 `suspected_source: "DART"` (IR을 ground truth로 가정).
       만약 운영자가 IR이 의심된다고 사전 표기한 케이스라면 escalate_to_human으로 분기.
  3. Invoke parser subagent (Agent tool, subagent_type=general-purpose):
       - 호출자 doc: parser_agent_doc 경로 (e.g. docs/agents/claude-agent-parser.md, 도메인 ref는 docs/domains/claude-agent-kics.md)
       - 메시지: "재파싱 요청 — 다음 항목의 raw source(suspected_source 기준)를
                  다시 확인하고 대상 JSON의 해당 row를 갱신해달라.
                  변경사항을 1줄 요약으로 회신."
       - packaging된 RED 묶음(suspected_source 포함)을 그대로 전달
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
- 2026-05-31: DART↔IR 교차검증 3개 룰 추가 — `CSM_WATERFALL_DART_VS_IR` (step별, tol=max(5%, 100억)), `SEGMENT_INSURANCE_INCOME_DART_VS_IR` (손보 장기/자동차/일반, tol=max(10%, 50억); 생보 SKIP), `CSM_BREAKDOWN_DART_VS_IR` (손보 보장성/물보험/저축성 or total, tol=max(5%, 100억)). 전부 RED → DART parser loopback. §1.4 IR-side input 계약 신설 (`data/ir/<period>/parsed/<KR>.json`). RED packaging에 `suspected_source` 필드 추가.
- 2026-05-30: 초안 작성. R1–R10, IFRS17 CSM 룰셋 codify. 공통 `QOQ_DELTA_WARN` 룰 추가 (threshold=15%, 누적 항목은 net 분기 기준). retry loop max=5 (IFRS17 reconcile 8→5).
