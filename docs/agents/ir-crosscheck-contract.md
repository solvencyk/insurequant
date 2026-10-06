# DART ↔ IR 교차검증 — IR-side 입력 계약 (휴면)

> 2026-10-07 `docs/agents/claude-agent-validation.md` §1.4 를 **무수정으로** 옮겼다. IR 정형 파싱이 owner 결정(2026-08-30 "꼭 필요할 때만")으로
> 보류돼 있어 이 계약을 쓰는 룰(`CSM_WATERFALL_DART_VS_IR`·`CSM_BREAKDOWN_DART_VS_IR`)은 전사 SKIP 이다. IR 파싱을 재개할 때 연다.

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

### 폐기된 룰 (참고)

| Rule | 사유 |
|---|---|
| ~~`SEGMENT_INSURANCE_INCOME_DART_VS_IR`~~ | **DEPRECATED (2026-06-01).** 부문별 보험손익 DART↔IR 비교는 **원천적으로 불가능**. 근거: IR이 공시하는 부문별 보험손익 = `부문별 보험서비스손익(DART 주석 추출 가능)` + `기타영업수익/기타사업비용을 IR 고유 키로 각 부문에 배분한 값`. DART는 기타영업수익·기타사업비용을 **전사 단일값**으로만 공시하고 부문 배분 키가 없어 IR 정의를 재현할 수 없음. 따라서 cross-source 비교 대신 **§1.5 `PL_BRIDGE_DART_INTERNAL`** (DART 자기완결 정합성)으로 대체. |
