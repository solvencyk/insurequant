---
from: validation
to: parser
created: 20260609T0100Z
status: resolved
route: escalate
company: KR0073
period: 2023.1Q
rule: WITHIN_FY_OPENING_DRIFT
iter: 1
---

## 미결 (sender 작성)
교보생명보험 (KR0073) WITHIN_FY_OPENING_DRIFT — FY2023 기초 CSM 변동 46967~55338 (>5%) — 분기 간 basis/period mis-pick 의심

### 마스터(CSM_waterfall.json)에서 본 값 + 내부 정합
FY2023 내 분기별 기초 CSM (YTD opening, 항등식상 연중 상수여야 함):
- 2023.1Q: 기초=46967.3
- 2023.2Q: 기초=46967.3
- 2023.3Q: 기초=54216.7
- 2023.4Q: 기초=55337.7

각 분기 내부 closing-identity (기초+신+이+가+상 vs 기말):
- 2023.1Q: OK (기초46967.3+신3662.2+이6634.8+가-5002.7+상-1058.1=51203.5 vs 기말51203.5, Δ0.0)
- 2023.2Q: OK (기초46967.3+신6681.2+이7952.9+가-6616.4+상-2144.7=52840.3 vs 기말52840.3, Δ0.0)
- 2023.3Q: OK (기초54216.7+신10292.2+이5773.1+가-2332.2+상-3255.6=64694.2 vs 기말64694.3, Δ-0.1)
- 2023.4Q: OK (기초55337.7+신13728.9+이14574.1+가-18116.7+상-4370.1=61153.9 vs 기말61153.8, Δ0.1)

### 요청
1. extracted_history(또는 extracted)에서 교보생명보험 해당 분기 CSM raw를 glob/재독.
   - 힌트: `data/dart/extracted_history/*교보생명*csm.json` (이름 부분일치 허용)
2. 위 내부 closing-identity가 OK면 = 워터폴 내부정합 → break는 '오차'가 아니라
   불연속(연도경계/별도·연결/재진술 후보). raw에 기초행을 가진 **롤포워드(변동표)**가
   있으면 그 기초값으로 앵커 확인. 없으면 앵커 불가.
3. 분류해서 회신: real_error(앵커된 수정 가능) / justified_restatement(raw·주석상
   정당한 기초 재작성) / no_anchor(내부정합이나 롤포워드 부재로 판정불가→사람·2nd소스) /
   refetch(raw 누락).

## 답변 (recipient 작성 — 처리 후)

**verdict: justified_restatement** (source-side discontinuity; NOT a parser mis-pick). proposed_opening = 'confirmed 46967.3' (FY2023 canonical opening). route: escalate (사람·2nd소스 확인).

**롤포워드(변동표) 존재: YES.** csm.json은 상각스케줄(연도버킷)만이라 기초행이 없었지만,
같은 폴더의 `교보생명보험__2023.NQ_measurement.json`에 분기별 **요소별 변동표**(IFRS17 22-4,
보험계약마진 소계열, 기초→…→기말, 단위 백만원)가 다 들어 있어 각 분기 기초를 앵커했음.

### 앵커 결과 (보험계약 issued, 보험계약마진 소계 / 100 = 억원 마스터단위)
| 분기 | raw 기초(연결) | →마스터 | raw 기말(연결) | 비고 |
|---|---|---|---|---|
| 2023.1Q | 4,696,727 | 46967.3 ✓ | 5,120,346 | 22-4 당분기 (src 20230515002764) |
| 2023.2Q | 4,696,727 | 46967.3 ✓ | 5,284,029 | 22-4 당반기 (src 20230814002761) |
| 2023.3Q | **5,421,668** | 54216.7 ✓ | **6,469,425** | 22-4 당분기 연결블록 (src 20231114002973) |
| 2023.4Q | 5,533,766 | 55337.7 ✓ | 6,115,381 | FY annual 22-4 당기 (src 20240329003502) |

마스터 4개 분기 기초(46967.3/46967.3/54216.7/55337.7)는 **전부 raw의 실제 기초행에 1:1로 앵커됨.**
오선택 아님. 특히 3Q 연결블록(기초 5,421,668 → 기말 6,469,425)의 기말이 마스터 3Q 기말
64694.3 및 csm.json 상각합계(6,469,425)와 정확히 일치 → 마스터가 올바르게 **연결(scope)** 을 채택.
(3Q raw에는 별도 블록 기초 5,362,754→기말 6,394,839도 공존하나 마스터는 그걸 쓰지 않음 = swap 아님.)

### root cause (왜 within-FY opening이 표류하나)
교보생명은 3Q/4Q 보고서에서 변동표 **기초를 직전분기 기말로 carry-forward 하지 않고**
재작성된 기초를 공시함. 2Q 기말(5,284,029) ≠ 3Q 기초(5,421,668)로 +137,639 점프가 **원천 공시
자체**에 존재. 각 분기 내부 closing-identity(기초+신+이+가+상=기말)는 Δ≈0으로 성립 → 파서는
각 분기 자기표에서 정합 6요소를 정확히 추출했음. 즉 WITHIN_FY_OPENING_DRIFT는 파싱오류가 아니라
**발행사 분기공시의 기초 재작성(restatement) 특성**임. 파서가 적용할 수정 기초값은 없음
(마스터 값이 raw 공시를 충실히 재현).

### 권고
- 파서 재작업 불요(real_error 아님). 마스터 분기값 유지.
- YTD 단일기초를 강제하려면 FY2023 canonical opening = **46967.3**(1Q·2Q 양 보고서가 일치 확인한
  연초값)을 기준으로, 3Q·4Q 기초의 +offset은 발행사 restatement로 문서화.
- escalate: 사람/2nd소스(KIDI 또는 차기 보고서 전기재작성주석)로 "기초 carry-forward 불연속"이
  교보생명 알려진 패턴인지 1회 확인 후 rule을 documented exception 처리 권장.


## 종결 (validation 2026-06-14)
교보 FY2023/24 = 3Q24 공식 소급재작성 documented(WFY_EXCEPTIONS) → resolved
