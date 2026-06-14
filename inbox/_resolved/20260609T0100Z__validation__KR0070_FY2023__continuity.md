---
from: validation
to: parser
created: 20260609T0100Z
status: resolved
route: escalate
company: KR0070
period: 2023.1Q
rule: WITHIN_FY_OPENING_DRIFT
iter: 1
---

## 미결 (sender 작성)
에이비엘생명보험 (KR0070) WITHIN_FY_OPENING_DRIFT — FY2023 기초 CSM 변동 7018~7585 (>5%) — 분기 간 basis/period mis-pick 의심

### 마스터(CSM_waterfall.json)에서 본 값 + 내부 정합
FY2023 내 분기별 기초 CSM (YTD opening, 항등식상 연중 상수여야 함):
- 2023.1Q: 기초=7017.8
- 2023.2Q: 기초=7017.8
- 2023.3Q: 기초=7017.8
- 2023.4Q: 기초=7585.3

각 분기 내부 closing-identity (기초+신+이+가+상 vs 기말):
- 2023.1Q: OK (기초7017.8+신604.3+이0.0+가154.8+상-226.6=7550.3 vs 기말7550.3, Δ0.0)
- 2023.2Q: OK (기초7017.8+신1655.3+이128.4+가524.6+상-486.2=8839.9 vs 기말8839.9, Δ0.0)
- 2023.3Q: OK (기초7017.8+신2778.5+이211.1+가475.6+상-751.8=9731.2 vs 기말9731.2, Δ0.0)
- 2023.4Q: OK (기초7585.3+신3475.9+이280.2+가-1716.3+상-929.7=8695.4 vs 기말8695.4, Δ0.0)

### 요청
1. extracted_history(또는 extracted)에서 에이비엘생명보험 해당 분기 CSM raw를 glob/재독.
   - 힌트: `data/dart/extracted_history/*에이비엘*csm.json` (이름 부분일치 허용)
2. 위 내부 closing-identity가 OK면 = 워터폴 내부정합 → break는 '오차'가 아니라
   불연속(연도경계/별도·연결/재진술 후보). raw에 기초행을 가진 **롤포워드(변동표)**가
   있으면 그 기초값으로 앵커 확인. 없으면 앵커 불가.
3. 분류해서 회신: real_error(앵커된 수정 가능) / justified_restatement(raw·주석상
   정당한 기초 재작성) / no_anchor(내부정합이나 롤포워드 부재로 판정불가→사람·2nd소스) /
   refetch(raw 누락).

## 답변 (recipient 작성 — 처리 후)

**verdict: no_anchor** (route: escalate → 사람/2nd소스)

**raw에 롤포워드(변동표) 있었나? — 없음 (NO).**

확인한 raw (READ-ONLY):
- `data/dart/extracted_history/에이비엘생명보험__2023.1Q_csm.json` → `[]` (테이블 0개)
- `..__2023.2Q_csm.json` → `[]` (0개)
- `..__2023.3Q_csm.json` → `[]` (0개)
- `..__2023.4Q_csm.json` → 테이블 16개, 그러나 **전부 연-버킷 상각스케줄표**
  ("보험계약마진 당기손익 인식구간", 컬럼=1년이내/1년초과2년이내/.../합계).
  기초·신계약·이자부리·조정·상각·기말 행을 가진 **롤포워드(변동표) 없음.**
  4Q표 원수 합계=869,543(당기말)/758,530(전기말) — 미래버킷별 잔액이지 기초값 아님.

**root cause (1-3줄):**
- 분기별 내부 closing-identity는 4개 분기 모두 OK(Δ0.0, sender 제공값 재확인). 따라서
  Q1-3 기초 7017.8 vs Q4 기초 7585.3 의 7018→7585 drift는 파서의 컬럼·별도/연결
  오선택이 아니라 **연중 기초 불연속**이다.
- FY2023 raw에는 기초행을 가진 롤포워드가 전무(Q1-3 추출 자체가 빈 배열, Q4는
  상각스케줄표만). 어느 기초값이 옳은지 raw로 **앵커 불가**. 재진술인지/단순 갱신인지도
  raw·주석만으로 단정 불가.
- 정직하게 보정값을 발명하지 않음 → no_anchor. 사람/2nd소스(연차보고서 CSM 변동표,
  KIDI·정기경영공시 롤포워드)로 7017.8/7585.3 중 정본 확정 필요.

**proposed corrected opening: n/a** (앵커 부재로 보정 미제시)

## 종결 (validation 2026-06-14)
ABL FY2023 = legit_restatement documented → resolved
