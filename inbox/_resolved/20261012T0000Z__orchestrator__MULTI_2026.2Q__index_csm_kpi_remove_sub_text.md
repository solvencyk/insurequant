---
from: orchestrator
to: designer
created: 20261012T0000Z
status: resolved
route: display
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-12 채팅): 「index.html 에 기말 CSM 에 주절주절 써놓은 거 빼라. 공시시점은 2026.2Q 로 이미 다른 데 적혀 있고, 47개사도 마찬가지로 다른 데 이미 있잖아」.

### 해 줄 것 (`index.html` 홈 KPI 「업계 총 기말 CSM」 카드 — 한 곳만)
- 값 아래에 붙은 부가 문구(현재 `2026.2Q · 47사` + `?` 정의 팝오버 `kpiCsmSub`·`kpiCsmHelp`·`help-kpi-csm`)를 **카드에서 제거**한다. 다른 KPI 카드(지급여력비율 중앙값·수록 보험사·기준 분기)와 같은 모양(값 + 라벨만)이 되게 한다. 옆 카드가 이미 「2026.2Q」(기준 분기)와 「47社」(수록 보험사)를 보여 주므로 중복이다.
- 값 계산(`industryCsmFromPanel`·`updateCsmKpi` 의 합산·모집단·폴백 로직)은 **바꾸지 않는다**. 문구·팝오버를 쓰던 코드와 마크업만 걷어내고, 더 이상 쓰이지 않는 변수·CSS 만 같이 정리한다(다른 곳에서 쓰는 `iq-help` 공통 스타일은 건드리지 말 것).
- 로직 주석에 적힌 「팝오버 문구」 언급이 있으면 사실에 맞게 한 줄로 고친다.
- 점검: 데스크톱·모바일(375px)에서 홈 KPI 4칸 높이·정렬이 어색하지 않은지, 값이 여전히 142조로 뜨는지, 콘솔 오류 0. 음수 △ 규칙 유지. `?iq_internal=1` 로 진입.

### 규칙
- 마스터 JSON·xlsx 수정 금지. 회사코드 노출 금지. `tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py`·`tests/test_prepush_scope.py` 통과 확인. 커밋은 자기 파일만(명시 경로, `git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json` 제외), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. push 금지(오케스트레이터 몫). 파이썬은 풀패스·스크립트 파일만. 서브에이전트 금지. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 변경 위치(줄), 점검 결과, 커밋 해시를 2~3줄로. `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
(designer 34a758d, orchestrator 검증·종결 2026-10-12) 홈 KPI 「업계 총 기말 CSM」 카드에서 부가 문구(기준 분기·회사 수)와 ? 팝오버 제거 — 값+라벨만. 합산·모집단·폴백 로직 불변, 미사용 .kpi-sub CSS 2줄 제거. 데스크톱 4칸 높이 83px 동일, 모바일 375px 2×2 가로 스크롤 0, 값 142조, 콘솔 오류 0. 테스트 3종 통과.
