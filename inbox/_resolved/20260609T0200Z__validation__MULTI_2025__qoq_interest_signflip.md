---
from: validation
to: parser
created: 20260609T0200Z
status: resolved
route: blind_spot
company: MULTI (동양생명 / 교보생명 / 코리안리재보험)
period: 2025
rule: QOQ_DELTA_WARN
iter: 1
---

## 미결 (validation 작성)

`QOQ_DELTA_WARN` 신규 구현 (`scripts/validate_master_tables.py` 4번). CSM waterfall 항목 시계열 이상탐지:
- 누적 항목(신계약/이자부리/상각) → **YoY**(전년 동기 YTD 대비, 분기 계절성 상쇄)
- 시점 항목(기말 CSM) → QoQ
- threshold: `config/qoq_thresholds.yaml` (신계약 30% / 이자부리 20% / 상각 10% / 기말 10%), floor 50억

전체 **193건 YELLOW**이나 대부분 사업상 변동(신계약 성장·금리 영향 이자부리 등)이라 noise. **진짜 데이터 의심 = 이자부리(순보험금융손익) 부호반전 3건**. CSM에 대한 이자부리는 통상 양수(accretion)인데 전년 양수 → 당기 음수로 뒤집힘:

| 회사 | 분기 | 이자부리 전년동기 → 당기 (억원) |
|---|---|---|
| 동양생명 | 2025.4Q | 1,134 → **−2,140** |
| 교보생명 | 2025.3Q | 3,242 → **−5,290** |
| 코리안리재보험 | 2025.2Q | 318 → **−116** |

요청: 위 분기 CSM 변동표의 **순보험금융손익(이자부리) 부호**를 raw에서 확인.
- 실제 음수면(금리·할인율 영향 가능) → 정상, close.
- 추출 시 부호/행 오선택이면 → 정정.

전체 QoQ 목록(193건, `sign_flip` 플래그 포함): `data/_derived/qoq_warn.json`

## 답변 (parser 작성 — 처리 후)

Three flagged rows, three different verdicts. 1 FIXED, 1 CLOSE-as-real, 1 ESCALATE.

**1) 동양생명 2025.4Q — extraction_error → FIXED.**
Parser picked the GRAND-TOTAL row "보험서비스결과 및 보험금융손익의 ... 총 변동" (CSM −228,193 백만) instead of the
finance line "보험금융손익 / 당기손익" (CSM +108,715 백만) — `extract_stages` sorts interest candidates by largest |value|,
so the aggregate row won. (2024 used a lettered A/B/C layout whose total rows don't contain "보험금융손익" → collision is
2025-label-form-specific.) Fix: added `INTEREST_AGG_MARKERS = ("보험서비스결과","총변동","총포괄손익")` guard in
`scripts/viz_build_csm_waterfall.py extract_stages()` (interest stage only). Result: item3 이자부리 −2139.9 → **+1105.0억**
(positive, matches 2024.4Q +1134; series now smooth). item4 (residual) absorbs the delta so closing identity holds.
Rebuilt root masters; diff confined to this ONE cell-pair (no other company/quarter changed); validate_master_tables +
continuity validator SUMMARY byte-identical (zero new findings). **Sign-flip resolved — re-validate.**

**2) 교보생명 2025.3Q — real_negative → CLOSE (downgrade to informational).**
The −5,289.6억 is genuine. The fair-value-measured (공정가치법) CSM column 보험금융손익 swung +206,695 → −624,435 백만
(a discount-rate / 금리 effect); parser read the parentheses-negative convention correctly and consistently in both years
(no sign inversion, no 재보험/전기 column). Closing identity confirms: 64380.6 + 9303.5 − 5289.6 − 4383.5 − 125.5(resid)
= 63885.4 = 당분기말 6,388,541 백만 ✓. No parser change. This is a true economic signal, not a data error.

**3) 코리안리재보험 2025.2Q — extraction_error, NOT auto-fixed → ESCALATE (tied to KR1000 basis note).**
−116.4억 = 순보험금융 base (+30.8억 / +3,077 백만) + 환율변동효과 (−147.2억 / −14,717 백만). pattern2 `find_interest()`
BUNDLES the FX line into 이자부리, while the pre-2025 `combined` path excludes it → the YoY +318 → −116 is apples-to-oranges,
not a real flip. True interest (2024-basis definition) = **+30.8억**. NOT applied because (a) the fix touches the shared
pattern2 path — code comment says the FX-add exists for 삼성생명 IR alignment, so removal needs a 삼성생명 regression check;
(b) it is entangled with the KR1000 FY2025 basis switch (same 2025 CER/pattern2 extraction). See inbox note
`...__KR1000_2025.1Q__continuity.md`. Recommended resolution under the chosen KR1000 basis; safer scope = route FX into
item4 (가정·경험 residual) rather than item3, validated against 삼성생명.

Net for this note: re-validate 동양 (fixed) and 교보 (close); 코리안리 carried into the KR1000 basis escalation.

## 종결 (validation 2026-06-14)
parser 3 verdict: 동양 2025.4Q FIXED(+1105)·교보 2025.3Q real_negative CLOSE·코리안리 2025.2Q escalate(KR1000 basis). 동양 재검증 통과 → resolved
