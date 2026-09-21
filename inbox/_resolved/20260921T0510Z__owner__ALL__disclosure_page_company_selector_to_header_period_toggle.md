---
from: owner
to: designer
created: 20260921T0510Z
status: resolved
route: design_change
company: ALL
period: ALL
rule: -
iter: 1
---

## 미결 (sender 작성)

owner 지시(2026-09-21, 원문): "기타공시 페이지도 마찬가지로 디자인 바꿔라." — K-ICS(`3573509`, 라이브)·IFRS17(`20260921T0500Z` 진행 중)과 **같은 헤더 셀렉트 + 같은 세그먼트 토글**을 `공시보고서.html` 에 적용한다.

지금 구조(HEAD 기준, `공시보고서.html`, 414줄):
- `<header>`(L90-100) 공유 헤더 동일. **이 페이지는 섹션 네비가 없다**(`.container` 에 `has-section-nav` 없음) — `--iq-hdr-h` 추종 대상은 없지만 헤더가 커져도 본문 첫 패널이 가려지지 않는지 확인.
- 첫 `.panel`(L102-106) `<h2>배당현황</h2>` + 설명 `<p>` + `#divCoverageLine`. **범위 밖, 그대로 둔다.**
- 둘째 `.panel .controls`(L108-116): `보험사: <select id="company">`(옵션은 JS L368-371 동적 생성, value=회사코드 KR…, 표시=약칭) · `기간: <select id="period">`(`quarter` 기본 selected / `year`) · `#reportThisBtn`. 아래 `#emptyHint`(`.coming-soon`) · `#dashHost`.
- JS 계약: `#company` L336-337(`onSelect`)·L368·L376·L390-391(URL `?company=` 자동선택), `#period` L239·L300(`||"quarter"` 폴백)·L378-379(change→`renderCompany`).

### 시킬 일

1. `#company` 셀렉트를 `<header>` 로 — IFRS17 티켓에서 `common.css` 로 승격한 헤더 셀렉트 클래스를 **그대로 재사용**(페이지 로컬 CSS 신설 금지). 이 페이지엔 키컬러 스와치가 없으니 점은 넣지 않는다.
2. `기간` 셀렉트를 `분기 | 연도` 세그먼트 토글로(기본 **분기**, 지금 기본값 유지). hidden `<select id="period">` `.sr-only` + `change` dispatch 패턴으로 L239·L300·L378 무수정. `role="radiogroup"`/`radio`/`aria-checked`, 키보드 ←→.
3. 컨트롤 패널에 토글 + 오류 제보 버튼만 남는다 — K-ICS·IFRS17 과 같은 배치로.
4. **검증(필수)** — 헤드리스(Playwright, 스크립트 안에서 임시 `http.server`): ① 1400px·375px 스크린샷, 스크롤 후 헤더 셀렉트 위치 고정 ② 회사 선택(배당 데이터 있는 회사, 예: `KR0069` 삼성생명 또는 옵션 첫 회사) → `#emptyHint` 숨고 KPI·표 렌더 ③ `연도` 토글 → `#divTableTitle`/표 열이 연도로, `#period.value==="year"`; 다시 `분기` ④ `?company=<코드>` 진입 반영 ⑤ ArrowRight 전환 ⑥ `scripts/validate_deployed_js.py --no-live` 4페이지 RED=0 · `pytest tests/test_deploy_assets.py -q` · pageerror 0. 스크린샷 `artifacts/designer_shots/20260921_disclosure_header_toggle/`.

제약: `git push` 금지·main 배포 금지. 커밋은 명시 pathspec(`공시보고서.html` + 필요 시 `common.css` + 문서·티켓). `scripts/`·마스터 JSON·`public_exports/` 금지. 데이터 인라인 금지. 음수 △. `TODO_designer.md` 맨 위 + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)


**처리 완료 (designer, 2026-09-21 · 오케스트레이터 세션 인계).**

1. **헤더 셀렉트** — `#company` 를 `<header>` 안 `.header-select-row` 로 이동(L100-104).
   IFRS17 티켓에서 `common.css` 로 승격한 클래스를 그대로 재사용했다 — 이 페이지에 새로 만든
   로컬 CSS 는 없다. 키컬러 스와치는 이 페이지에 없으므로 점도 넣지 않았다.
2. **`기간` 세그먼트 토글** — `분기 | 연도`(기본 분기). `<select id="period">` 는 `.sr-only` 로 남겨
   L239·L300·L378 무수정. `role="radiogroup"`/`radio`/`aria-checked`, ←→ 키(`setupSegToggle`, L192-225).
3. 컨트롤 패널에는 토글 + 오류 제보 버튼만 남겼다 — K-ICS·IFRS17 과 같은 배치.
4. **검증(헤드리스 Playwright, 1400px·375px)**:
   ① 2,000px 스크롤 후 헤더 셀렉트 `visibleAfterScroll=true`(데스크톱 top=72 / 모바일 top=68)
   ② 첫 회사 `KR0001` 선택 → `#emptyHint` 숨김·`#dashHost` 표시
   ③ `연도` 토글 → `#period.value==="year"`; ArrowLeft → `quarter` 복귀
   ④ 이 페이지는 섹션 네비가 없다 — 대신 헤더가 118px(데스크톱)/112px(모바일)로 커진 뒤에도
      본문 첫 패널이 안 가리는지와 `scrollTo(0)` 이 0 에 닿는지 확인(`topReach=0`).
      `scroll-padding-top` 이 실측 추종으로 바뀌어 130px/124px 로 따라온다.
   ⑤ `validate_deployed_js.py --no-live` 4페이지 **RED=0**, `pytest tests/test_deploy_assets.py` 11 passed,
      uncaught pageerror 0 (GA4 CSP 콘솔 에러는 4페이지 공통 기존 조건, 무관)
   스크린샷: `artifacts/designer_shots/20260921_header_toggle_v2/`

`?company=` 자동선택(L390-391)은 셀렉트가 헤더로 옮겨가도 같은 `#company` 를 잡으므로 무변경이다.
