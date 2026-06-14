---
from: validation
to: parser
created: 20260609T0100Z
status: resolved
route: escalate
company: KR0011
period: 2023.1Q
rule: WITHIN_FY_OPENING_DRIFT
iter: 1
---

## 미결 (sender 작성)
DB손해보험 (KR0011) WITHIN_FY_OPENING_DRIFT — FY2023 기초 CSM 변동 116435~122497 (>5%) — 분기 간 basis/period mis-pick 의심

### 마스터(CSM_waterfall.json)에서 본 값 + 내부 정합
FY2023 내 분기별 기초 CSM (YTD opening, 항등식상 연중 상수여야 함):
- 2023.1Q: 기초=118270.3
- 2023.2Q: 기초=122497.3
- 2023.3Q: 기초=117348.9
- 2023.4Q: 기초=116434.9

각 분기 내부 closing-identity (기초+신+이+가+상 vs 기말):
- 2023.1Q: OK (기초118270.3+신6858.8+이831.0+가-2701.7+상-3294.7=119963.7 vs 기말119963.7, Δ0.0)
- 2023.2Q: OK (기초122497.3+신13529.4+이1783.7+가-4754.1+상-6706.5=126349.8 vs 기말126349.8, Δ0.0)
- 2023.3Q: OK (기초117348.9+신21253.1+이2675.4+가-6032.9+상-9411.7=125832.8 vs 기말125832.9, Δ-0.1)
- 2023.4Q: OK (기초116434.9+신28261.2+이3644.0+가-14196.8+상-12619.3=121524.0 vs 기말121524.1, Δ-0.1)

### 요청
1. extracted_history(또는 extracted)에서 DB손해보험 해당 분기 CSM raw를 glob/재독.
   - 힌트: `data/dart/extracted_history/*DB손해*csm.json` (이름 부분일치 허용)
2. 위 내부 closing-identity가 OK면 = 워터폴 내부정합 → break는 '오차'가 아니라
   불연속(연도경계/별도·연결/재진술 후보). raw에 기초행을 가진 **롤포워드(변동표)**가
   있으면 그 기초값으로 앵커 확인. 없으면 앵커 불가.
3. 분류해서 회신: real_error(앵커된 수정 가능) / justified_restatement(raw·주석상
   정당한 기초 재작성) / no_anchor(내부정합이나 롤포워드 부재로 판정불가→사람·2nd소스) /
   refetch(raw 누락).

## 답변 (recipient 작성 — 처리 후)

**verdict: no_anchor** (route: escalate → 사람/2nd 소스)

### raw에 롤포워드(변동표)가 있었나? — 없음
data/dart/extracted_history/DB손해보험__2023.{1,2,3,4}Q_csm.json 4개 모두 확인.
모든 표가 "...보험계약마진의 **연도별 인식시기**(amortization schedule, year-bucket)"
캡션의 A_rows 표뿐임 (행: 보험계약마진 잔액 / 1년미만 / 1년이상 2년미만 / ...).
**기초·신계약·이자부리·조정·상각·기말 행을 가진 변동표(롤포워드)는 4개 파일 어디에도
없음** (기초|신계약|이자부리|변동 grep = 0 hit). 따라서 단일 canonical FY2022 기말
opening을 raw로 앵커할 수단이 없음. fallback인 data/dart/extracted/ 에도 DB손해 FY2023
파일은 없음(2025 filing만 존재) → refetch 대상도 아님(raw는 정상 존재·판독 가능).

### root cause (파서 mis-pick 아님 — 원천 재진술)
파서 픽은 raw에 충실함. master = 발행(item34-5) **장기 컬럼 ÷100**(raw 백만 → master 억):
- master 기말(item6) = raw 발행 장기 **당기말**/100 — 4분기 전부 정확 일치
  (예 1Q 11,996,372/100 = 119,963.7 = master 119963.7).
- master 기초(item1, 룰이 보는 YTD-opening) = raw 발행 장기 **전기말**/100 — 4분기 전부 정확 일치
  (1Q 11,827,029/100=118270.3 / 2Q 12,249,728/100=122497.3 /
   3Q 11,734,886/100=117348.9 / 4Q 11,643,492/100=116434.9).

즉 YTD-opening 드리프트(118270.3→122497.3→117348.9→116434.9)는 파서 오선택이 아니라
**DB손해가 FY2023 각 분기 공시에서 비교표시 전기말(=FY2022 기말) 컬럼 자체를 분기마다
다르게 재진술**한 결과를 그대로 받아온 것. 내부 closing-identity는 4분기 모두 OK(sender 확인),
QTD-opening 체인(값_당분기 item1)도 직전 분기 기말과 분기간 완전 연속
(1Q기말119963.7=2Q QTD기초 / 2Q기말126349.8=3Q QTD기초 / 3Q기말125832.9=4Q QTD기초).
드리프트는 오로지 YTD-opening 컬럼에만 존재.

### proposed corrected opening
**n/a** — 원천이 전기말을 4개 서로 다른 값으로 제시하고, 어느 것이 진짜 재진술 후
opening인지 가려줄 변동표(롤포워드)가 raw에 없음. 정직성 제약상 임의 보정값을 만들지 않음.
사람/2nd 소스(예: DART 본문 변동표·사업보고서 주석, 또는 FY2022 사업보고서 기말 CSM)로
canonical FY2022 기말 opening 1개를 확정해야 함. justified_restatement로 굳히려면 그
2nd 소스의 변동표/재진술 근거가 필요(현재 raw만으로는 입증 불가).

## 종결 (validation 2026-06-14)
DB손해 FY2023 re-anchor(override 18셀, parser 답변)로 해소·WFY 통과 → resolved
