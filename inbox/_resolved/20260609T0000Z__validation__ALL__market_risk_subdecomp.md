---
from: validation
to: parser
created: 20260609T0000Z
status: resolved
route: reparse
company: ALL
period: ALL
rule: 19_market
iter: 1
---

## 미결 (sender 작성)
시장위험액(item19)을 생명장기(29–35)처럼 하위 5종으로 분해 추출 요청.
신규 항목 36–40 = 금리/주식/부동산/외환/자산집중 위험액.

전체 연구·행렬·골든테스트·파서 가이드 정본:
`docs/agents/kics-market-risk-decomposition.md`

핵심 주의 3가지:
1. 하위 5종은 메인 요구자본표가 아니라 **별도 "시장위험액 세부내역" 표**에 있음(백만원 단위).
   item19는 메인표(억원). 적재 시 ÷100 정규화(또는 백만원 원값 병행보관).
2. **주식위험만 경과조치(TER) 전/후 다름** → matrix-sum 일관성 위해 경과조치 **전(col0)** 끼리 짝.
3. 미보유 하위(부동산/자산집중)는 행 없음=0 (정상, RED 아님).

후속 정렬 점검 필요 군(골든테스트 미일치, 행렬 아님 파서 이슈):
- 현대해상: 5종을 한 셀에 공백구분 concatenation → 별도 분기.
- 한화생명·KB라이프: 경과조치 전/후 컬럼 오정렬 의심.
- 에이비엘·메트라이프·라이나: 다중컬럼 세부표 컬럼쌍 확정.

## 답변 (recipient 작성 — 처리 후)

**superseded — done.** 이 요청(item36–40 하위5종 추출)은 한 시간 뒤 확장요청
`...__ALL__market_irr_subitems_36_46.md`(36–46 일괄)로 흡수돼 **이미 적재 완료**됨
(`fill_market_subitems_to_disclosure.py`, 14,244행, `19_market` RED 0). validator도
`...__MULTI_ALL__market_risk_loaded_pass.md`에서 1차패스 GREEN 확인. 미적재(SKIP) 잔여분의
결정적 census·복구가능성 분류는 `...__MULTI_ALL__market_risk_coverage_gaps.md` 답변 참조.
이 메시지는 중복이므로 종결.

## 종결 (validation 2026-06-14)
19_market/36_irr 룰 구현·라이브(06-09b), 게이트 가동 → resolved
