---
from: validation
to: parser
created: 20260609T0100Z
status: resolved
route: reparse
company: KR0072
period: 2023.1Q
rule: WITHIN_FY_OPENING_DRIFT
iter: 1
---

## 미결 (sender 작성)
케이디비생명보험 (KR0072) WITHIN_FY_OPENING_DRIFT — FY2023 기초 CSM 변동 5239~5696 (>5%) — 분기 간 basis/period mis-pick 의심

### 마스터(CSM_waterfall.json)에서 본 값 + 내부 정합
FY2023 내 분기별 기초 CSM (YTD opening, 항등식상 연중 상수여야 함):
- 2023.1Q: 기초=5239.4
- 2023.2Q: 기초=5239.4
- 2023.3Q: 기초=5239.4
- 2023.4Q: 기초=5695.9

각 분기 내부 closing-identity (기초+신+이+가+상 vs 기말):
- 2023.1Q: n/a (missing item)
- 2023.2Q: OK (기초5239.4+신1174.0+이90.0+가-685.5+상-234.2=5583.7 vs 기말5583.7, Δ0.0)
- 2023.3Q: OK (기초5239.4+신2210.7+이146.1+가-1912.9+상-352.5=5330.8 vs 기말5330.8, Δ-0.0)
- 2023.4Q: OK (기초5695.9+신3023.1+이183.4+가-2560.0+상-512.0=5830.4 vs 기말5830.5, Δ-0.1)

### 요청
1. extracted_history(또는 extracted)에서 케이디비생명보험 해당 분기 CSM raw를 glob/재독.
   - 힌트: `data/dart/extracted_history/*케이디비*csm.json` (이름 부분일치 허용)
2. 위 내부 closing-identity가 OK면 = 워터폴 내부정합 → break는 '오차'가 아니라
   불연속(연도경계/별도·연결/재진술 후보). raw에 기초행을 가진 **롤포워드(변동표)**가
   있으면 그 기초값으로 앵커 확인. 없으면 앵커 불가.
3. 분류해서 회신: real_error(앵커된 수정 가능) / justified_restatement(raw·주석상
   정당한 기초 재작성) / no_anchor(내부정합이나 롤포워드 부재로 판정불가→사람·2nd소스) /
   refetch(raw 누락).

## 답변 (recipient 작성 — 처리 후)

**verdict: justified_restatement** (proposed_opening: 5239.4·5695.9 둘 다 confirmed — 마스터 유지)

**롤포워드 유무:** csm.json(예상 인식기간 = year-bucket 상각표)에는 기초행 **없음**.
그러나 **measurement.json에 기초행을 가진 CSM 변동표(보험계약마진 컬럼)가 있어 두 기초값 모두 앵커됨.**

**root cause (불연속 = 오차 아님, 분기보고서 vs 사업보고서 기초 basis 차이 = 재진술):**
- 1Q·2Q·3Q 기초 5239.4 = 분기보고서(제36기 X분기) 변동표 **기초 보험계약마진 523,940 백만원**.
  세 분기 measurement 모두 기초 523,940 (YTD 연중상수, 정상). 1Q 분기말 472,725 = 마스터 기말 4727.2 일치.
- 4Q 기초 5695.9 = 사업보고서(제36당기) 변동표 **기초 보험계약마진 569,595 백만원** (= 제35전기 감사 기말).
- 즉 원천에 **두 개의 서로 다른 기초가 실제로 공시**됨: 분기 523,940 vs 연차 569,595
  (차이 +45,655 백만원 ≈ +8.7%). 이는 분기-연차 간 **기초 CSM 재진술**이지 파서 오선택/별도-연결 swap/off-by-year 아님.

**앵커 검증:** 각 분기 기말(마스터)은 해당 분기 csm.json **발행 보험계약 합계**와 일치
(1Q 472,724 / 2Q 558,367 / 3Q 533,082 / 4Q 583,047 백만원 → 4727.2/5583.7/5330.8/5830.5).
각 분기 기초도 자기 분기 measurement 변동표 기초행과 일치. 내부 closing-identity 전분기 OK.

**결론:** 마스터값 수정 불필요. WITHIN_FY_OPENING_DRIFT는 진성 재진술(분기 vs 연차 basis)이므로
이 회사·연도에 한해 **documented exception**으로 통과 처리 권고 (re-fetch/re-parse 불요).
참고: src measurement.json은 csm slot이 아닌 measurement slot에 변동표가 들어있어, 향후
WITHIN_FY 드리프트 진단 시 measurement.json의 보험계약마진 기초/기말 컬럼을 같이 보면 자동 앵커 가능.

## 종결 (validation 2026-06-14)
케이디비 FY2023 = legit_restatement documented → resolved
