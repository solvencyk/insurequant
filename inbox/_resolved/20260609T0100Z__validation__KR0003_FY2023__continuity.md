---
from: validation
to: parser
created: 20260609T0100Z
status: resolved
route: escalate
company: KR0003
period: 2023.2Q
rule: WITHIN_FY_OPENING_DRIFT
iter: 1
---

## 미결 (sender 작성)
롯데손해보험 (KR0003) WITHIN_FY_OPENING_DRIFT — FY2023 기초 CSM 변동 16774~18005 (>5%) — 분기 간 basis/period mis-pick 의심

### 마스터(CSM_waterfall.json)에서 본 값 + 내부 정합
FY2023 내 분기별 기초 CSM (YTD opening, 항등식상 연중 상수여야 함):
- 2023.2Q: 기초=18004.6
- 2023.3Q: 기초=16774.4
- 2023.4Q: 기초=16774.4

각 분기 내부 closing-identity (기초+신+이+가+상 vs 기말):
- 2023.2Q: OK (기초18004.6+신2651.0+이377.9+가-556.7+상-843.4=19633.4 vs 기말19633.5, Δ-0.1)
- 2023.3Q: OK (기초16774.4+신4092.1+이554.0+가1981.3+상-1316.2=22085.6 vs 기말22085.6, Δ0.0)
- 2023.4Q: OK (기초16774.4+신5478.9+이780.5+가2801.0+상-1868.5=23966.3 vs 기말23966.2, Δ0.1)

### 요청
1. extracted_history(또는 extracted)에서 롯데손해보험 해당 분기 CSM raw를 glob/재독.
   - 힌트: `data/dart/extracted_history/*롯데손해*csm.json` (이름 부분일치 허용)
2. 위 내부 closing-identity가 OK면 = 워터폴 내부정합 → break는 '오차'가 아니라
   불연속(연도경계/별도·연결/재진술 후보). raw에 기초행을 가진 **롤포워드(변동표)**가
   있으면 그 기초값으로 앵커 확인. 없으면 앵커 불가.
3. 분류해서 회신: real_error(앵커된 수정 가능) / justified_restatement(raw·주석상
   정당한 기초 재작성) / no_anchor(내부정합이나 롤포워드 부재로 판정불가→사람·2nd소스) /
   refetch(raw 누락).

## 답변 (recipient 작성 — 처리 후)

**verdict: justified_restatement** (route: escalate — 사람/2nd소스 확인용으로 큐잉, 자동수정 대상 아님)

**raw에 롤포워드(변동표) 있었나? → 예.** `*_measurement.json`에 직접계약 BEL/RA/CSM 측정요소별 변동표가 분기별로 존재. CSM 합계 = 변동표 CSM "소계" 컬럼. csm.json은 year-bucket 상각스케줄뿐이라 앵커 불가하지만, measurement.json의 변동표 기초행이 앵커가 됨.

**앵커 결과 (raw 기초 CSM 소계, 단위 백만원 → master 억원 = ÷100):**
- 2023.2Q `<제79(당)기 반기>` 기초순보험계약부채 CSM소계 = **1,800,463** → 18,004.63 → master 18004.6 **일치**
- 2023.3Q `<제79(당)기 3분기>` 기초순보험계약부채 CSM소계 = **1,677,438** → 16,774.38 → master 16774.4 **일치**
- 2023.4Q `<제79(당)기>` 기초순보험계약부채 CSM소계 = **1,677,438** → 16,774.38 → master 16774.4 **일치**

**root cause:** 파서 mis-pick 아님. 세 분기 모두 각 공시 직접계약 변동표의 기초행 CSM 소계를 정확히 옮긴 값(컬럼·연결/별도·연도 오류 없음). 마스터 내부 closing-identity도 전분기 OK. 불연속의 정체는 **FY2023 기초(전기말 2022.12.31) CSM 자체가 반기→3분기 공시 사이에 재진술**된 것 — 반기 공시는 기초 1,800,463 백만원, 3분기·연간 공시는 동일 기초를 1,677,438 백만원으로 하향 재작성(Δ ≈ -1,230억 / -6.8%). 두 값 모두 raw 충실 전사이므로 '오차'가 아님. (재진술 사유 — 가정변경/소급재작성 — 의 명시 주석은 본 CSM·measurement raw 발췌 범위 밖이라 미확인 → 사람/2nd소스 확인 권장하여 escalate.)

**proposed_opening: confirmed 16774.4** (3분기·연간 공시가 일치시킨 재진술 후 FY2023 기초값. 마스터는 이 값 유지가 맞고, 2023.2Q의 18004.6은 반기 원공시 기초로 그 자체는 정확한 전사임 — 분기 간 drift는 재진술에 기인한 정당한 불연속).

## 종결 (validation 2026-06-14)
continuity validator 재실행: KR0003 더는 RED 아님 → resolved
