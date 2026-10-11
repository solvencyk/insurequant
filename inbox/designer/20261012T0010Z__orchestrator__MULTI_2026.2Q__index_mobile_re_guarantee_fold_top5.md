---
from: orchestrator
to: designer
created: 20261012T0010Z
status: open
route: display
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-12 채팅): 「모바일에 index.html 에서 보증·재보험사 부분도 상위 5개만 보이게 하고 더보기 기능 활성화 (생보·손보처럼)」. 같은 날 앞 티켓(`20261012T0000Z`, 홈 KPI 카드 부가 문구 제거)을 처리한 **뒤에** 이어서 처리한다(같은 `index.html`이라 동시 편집 금지, 커밋은 티켓별로 따로).

### 현황(조사 결과, `index.html`)
- `FOLDABLE = { 'Life': true, 'Non-Life': true, 'Re': false }`(약 965행) — 재보험(`Re`) 섹터는 접기 대상에서 **명시적으로 제외**돼 있어 모바일에서 전 회사가 다 보인다. 보증(서울보증)은 한 곳이라 접을 일이 없고, 재보험·보증 묶음 그룹이 어디에 속하는지는 `GROUPED`/`SEG_ORDER`/`SEG_LABEL` 정의로 확인할 것.
- 접기 상태는 `lifeExpanded`/`nonlifeExpanded`(K-ICS 마켓맵 리스트 `renderList`, ~966–1034행)와 `bubbleLifeExpanded`/`bubbleNonlifeExpanded`(CSM 버블맵 리스트 `renderBubbleList`, ~1396–1495행)로 섹터 2개만 따로 들고 있고, 버튼 문구는 `더보기 (N개사)` / `접기`, `FOLD = 5`.

### 해 줄 것
- 모바일(<640px)에서 **재보험·보증 그룹도 상위 5개만** 보이고 `더보기 (N개사)` / `접기` 버튼이 생기게 한다. 생보·손보와 같은 동작·같은 모양. 정렬 기준·maxV 섹터 독립(막대 길이는 보이는 항목 기준)도 같은 규칙. 데스크톱은 변하지 않는다.
- 위 두 리스트(K-ICS 마켓맵 리스트, CSM 버블맵 하단 리스트)에 **모두** 적용. 섹터별 expanded 상태를 하드코딩 변수 쌍 대신 섹터 키 맵으로 일반화하는 정도의 최소 수정으로 한다(과도한 리팩터 금지). `redraw`/탭 전환/섹터 필터 변경 시 접힘으로 되돌리는 기존 동작을 새 섹터에도 같게 맞춘다.
- 회사가 5개 이하인 그룹은 버튼이 안 생긴다(기존 규칙 그대로). 접힌 상태에서 순서·`aria` 속성이 기존과 같은지 확인.
- 점검: 모바일 375px 에서 K-ICS 리스트와 CSM 버블 리스트 각각 재보험 그룹이 5개 + `더보기 (N개사)` 로 보이는지, 누르면 전체·`접기`로 바뀌는지, 생보·손보 동작 회귀 0, 콘솔 오류 0, 가로 스크롤 0. 스크린샷 경로 보고.

### 규칙
- 마스터 JSON·xlsx 수정 금지. 회사코드 노출 금지. `tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py`·`tests/test_prepush_scope.py` 통과. 커밋은 자기 파일만(명시 경로, `git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json` 제외), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. push 금지. 파이썬은 풀패스·스크립트 파일만. 서브에이전트 금지. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 변경 위치(줄), 점검 결과·스크린샷 경로, 커밋 해시를 2~3줄로. `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
