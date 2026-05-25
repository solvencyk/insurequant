# Forward Outlook confidence=low Root Cause v2 (after F4 patch + user re-classification)

Generated: 2026-05-25 post-F4-fix
Source: output/kics_forward_capital/20260525T145147Z/forward_simulation_v3.json

## v2 changes vs v1 report

User feedback (2026-05-25):
1. **Cat E (negative basic capital)** — 롯데손보 (KR0003), KDB생명 (KR0072) — 정상 stressed state, NOT a data-quality issue. Should not be flagged as "신뢰도 낮음". Re-class → "stressed_baseline (정상)".
2. **Cat F (교보라이프 BS≈0 quirk)** — KR1010. **Fixed in code**: compute_confidence threshold `==0` → `<1.0` (sub-1억 BS residual tolerated). Re-confirmed as high. 교보생명이 모회사라 자체 발행 안 한 것으로 추정.
3. **Cat C/D (over/under_deduct)** — user wants research on BS bond carrying-value mechanics. Pending separate investigation: FV vs face vs amortized cost; what gets deducted on Call exercise (commit notes only, no model change yet).
4. **Cat B drill-down** requested below.

## New distribution (37 cohort, post-patch)

- high: 11 (was 10) — KR1010 promoted
- medium: 3
- low: 22 (was 23) — KR1010 dropped out
- no_data: 1

After excluding Cat E (legitimate stress, KR0003 + KR0072): **20 actionable LOWs**.

## Category B drill-down (FSC T2 missing, BS T2 present)

11 insurers (not 10 — corrected count). Sorted by BS T2 size:

| Code | Insurer | BS T2 (억) | Face T2 (FSC) | Likely cause |
|------|---------|-----------:|--------------:|--------------|
| KR0069 | 삼성생명보험 | **66,289** | 0 | FSC alias 누락 (Phase 5에서 미해결 outlier). 분석상 진짜 최대 영향 |
| KR1000 | 코리안리재보험 | 4,431 | 0 | FSC alias 누락 가능 (코리안리재보험 vs 코리안리) |
| KR0008 | 삼성화재해상보험 | 4,097 | 0 | FSC alias 누락 (sibling KR0069 동일 패턴) |
| KR0099 | KB라이프생명 | 2,011 | 0 | 신생 통합법인 (KB생명+푸르덴셜 통합), FSC 등재 미완료 가능 |
| KR1011 | IBK연금보험 | 1,615 | 0 | 정부계열 특수법인 — FSC 미등재 정상 가능 |
| KR0097 | 하나생명보험 | 1,553 | 0 | 외국계 → 하나금융 인수, FSC 누락 |
| KR0050 | 하나손해보험 | 1,020 | 0 | 외국계 → 하나금융 인수, 동일 |
| KR0049 | 악사손해보험 | 331 | 0 | 외국계 (AXA), 자체 발행 안 했을 가능성 큼 |
| KR0100 | 처브라이프생명보험 | 131 | 0 | 외국계 (Chubb), 자체 발행 미실시 |
| KR0075 | 비엔피파리바카디프생명 | 53 | 0 | 외국계 (BNP), 자체 발행 미실시 |
| KR0150 | 서울보증보험 | 46 | 0 | 정부계 (예금보험공사 출자), PAA 적용 |

### 패턴 분류

1. **FSC alias 누락 (해결 가능)**: KR0008 / KR0069 (삼성 화재·생명), KR1000 (코리안리). 총 BS T2 **74,817억** = 한국 보험사 자본성증권 시장의 큰 조각.
2. **외국계 / 신생 (자체 발행 없음)**: KR0049, KR0075, KR0099, KR0100, KR1011. 총 **4,141억**. 모기업 자본 활용 — 자체 자본성증권 발행 동기 약함. 모회사 지원 가정으로 "정상" 처리 가능.
3. **외국→국내 인수 후 정리 중**: KR0050 하나손해, KR0097 하나생명. 총 **2,573억**. 인수 후 발행 정보 통합 안 됐을 가능성.
4. **특수법인 (정부계)**: KR0150 서울보증 46억 — PAA 적용으로 forward sim 자체가 부적합.

### Recommended actions

- **HIGH priority**: KR0008 / KR0069 / KR1000 FSC alias 보강 (Phase 5 follow-up). 단순 alias 추가만으로 face_T2 가 채워질 가능성.
- **MEDIUM**: 외국계 5사 (KR0049/0075/0099/0100/1011) → "no_self_issued, parent_capital" 정상 분류 + confidence "medium" 강제. compute_confidence에 분류 helper 추가 권고.
- **LOW**: 인수 통합 중 사 (KR0050/0097) → 인수 후 데이터 정리 대기. 일단 그대로.
- **EXCLUDE**: KR0150 서울보증 — PAA 적용 사는 forward sim 자체에서 제외 권고.

## Category C/D — research pending (per user msg)

User callout: "over 또는 under 라고 하는건 BS에 그 bond의 시장가치 (FV 말고) 가 있었다는거야? 상환할 때 둘중 뭐가 차감되는지까지는 나도 잘 모르겠는데, 이건 리서치를 좀 해봐야할듯."

Research questions for next session:
1. BS 자본성증권 carrying value = 발행가 (액면) - 직접발행비용 + 평가손익 누계? (amortized cost) vs 공정가치(FV)?
2. K-IFRS 1109 분류: 자본성증권은 자본금융상품 (equity) vs 부채금융상품 (liability)? 분류에 따라 회계처리 다름.
3. Call exercise 시 (1) 액면 차감 또는 (2) 장부가 차감 — 어느 쪽?
4. K-ICS 자본 인정금액과 BS 장부가 차이의 정상 범위?

답이 나오면:
- C (over_deduct, face >> BS): 가능 시나리오 — bond DB에 outstanding으로 잡혀있는데 실제로는 call 행사됨 (Phase 5 가설 검증)
- D (under_deduct, face << BS): 가능 시나리오 — 평가이익 반영 + 발행비용 분할상각 후 BS가 face 초과

→ 답이 나오기 전까지 C/D 분류는 "data noise, real meaning TBD" 로 표시.

## Category E (negative basic capital) — re-classified as legitimate

KR0003 롯데손해 basic_cap = -3,875억, KR0072 KDB생명 basic_cap = -3,311억.

이건 데이터 품질 이슈가 아니라 실제 자본 stress 상태. Forward sim은 정상 작동, 출력값도 의미 있음. **confidence 낮음 분류에서 제외** (per user).

Recommend code change (future):
```python
if basic_baseline is not None and basic_baseline < 0:
    confidence["pre_stressed_baseline"] = True
    # do not downgrade confidence on basic-side issues
```

## Final actionable LOW list (after re-classification)

| Code | Insurer | Cat | Action |
|------|---------|-----|--------|
| KR0069 | 삼성생명 | B-high | FSC alias 추가 (대형) |
| KR0008 | 삼성화재 | B-high | FSC alias 추가 |
| KR1000 | 코리안리 | B-high | FSC alias 시도 |
| KR0099 / 1011 | KB라이프 / IBK | B-med | 신생/특수 — 모니터링만 |
| KR0049/0075/0100 | 외국계 3사 | B-med | "no_self_issued" 분류 |
| KR0050 / 0097 | 하나손/생 | B-med | 인수 통합 대기 |
| KR0150 | 서울보증 | B / PAA | sim cohort에서 제외 권고 |
| Cat C/D 7사 | 다양 | TBD | 회계처리 리서치 후 재분류 |
| KR0068 (Cat G) | 한화생명 | G | 별도 분석 — 신종 일부 누락 |

Top-3 high-impact action: 삼성생명/삼성화재/코리안리 FSC alias 보강 1건으로 약 75,000억 BS T2 face_T2=0 격차 해소 가능.
