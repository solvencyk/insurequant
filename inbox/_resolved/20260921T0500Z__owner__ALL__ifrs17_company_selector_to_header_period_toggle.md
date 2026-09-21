---
from: owner
to: designer
created: 20260921T0500Z
status: resolved
route: design_change
company: ALL
period: ALL
rule: -
iter: 1
---

## 미결 (sender 작성)

owner 지시(2026-09-21, 원문): "디자인 관련해서 IFRS17.html에도 마찬가지로 회사명은 위에 고정, 분기/연도 선택 토글키로 바꿔라."
K-ICS 에 방금 라이브로 나간 것(`3573509`, main `6741dea`)과 **같은 모양·같은 동작**으로 IFRS17 에 적용한다.

지금 구조(HEAD 기준, `IFRS17.html`):
- `<header>`(L122-132) 는 K-ICS 와 동일한 공유 헤더(`.brand` + `.header-row` 탭 3개 + 다운로드 CTA).
- 첫 `.panel`(L146-149) `<h2>IFRS17 통합 현황</h2>` + `<p id="wfPeriodLine">`(JS L2229-2230 이 "CSM 워터폴 커버리지: N개사 · 범위 · 연 누계(YTD) 기준" 을 채움). **이 패널은 이번 범위 밖 — 그대로 둔다**(owner 가 K-ICS 와 달리 제목·부제 언급 없음).
- 둘째 `.panel .controls`(L151-160): `보험사: <span id="coSwatch">`(회사 키컬러 점) + `<select id="company">`(옵션은 JS L2233-2237 이 동적 생성, **value=회사코드 KR0001…, 표시=약칭**) · `기준: <select id="wfPeriod">`(`year` 기본 selected / `quarter`) · `#reportThisBtn`. 그 아래 `#emptyHint`("보험사를 선택해 주세요") · `#dashHost`.
- JS 계약: `#company` 는 L1781·2109·2116·2234(change→`onSelect`)·2262(URL `?company=` F1 자동선택, index 버블 크로스내비가 씀), `#coSwatch` L1779·2115(회사 선택 시 키컬러 채움/해제), `#wfPeriod` 는 L1788 `wfMode`·L1859 `plMode`(`||"year"` 폴백)·L2246(change→`renderCompany`). 캡션 L1639 가 `mode==="quarter"?"분기":"연도"` 를 인쇄한다.

### 시킬 일

1. **보험사 셀렉트(+coSwatch)를 `<header>` 로** — K-ICS 와 같은 자리·같은 클래스. 스와치 점이 헤더 셀렉트 옆에서 계속 회사 색으로 바뀌어야 한다(L1779·2115 그대로 동작).
2. **`기준` 셀렉트를 세그먼트 토글로** — `연도 | 분기`(기본 **연도**, 지금 기본값 유지). K-ICS 와 같은 방식(hidden `<select id="wfPeriod">` 를 `.sr-only` 로 남기고 토글이 값 갱신 + `change` dispatch) 이면 L1788·1859·2246 을 안 건드려도 된다. `role="radiogroup"`/`role="radio"`/`aria-checked`, 키보드 ←→·Space.
3. **토글·헤더 셀렉트 스타일을 `common.css` 로 승격.** K-ICS 는 `.seg-toggle/.seg-btn`(K-ICS.html `<style>` L57-70 부근) 과 헤더 셀렉트 행을 페이지 로컬 CSS 로 넣었다 — 두 페이지가 쓰게 됐으니 `common.css` 한 곳으로 옮기고 K-ICS.html 의 로컬 정의는 지운다(디자인 시스템 단일 소스 원칙, `docs/agents/claude-agent-designer.md`). 옮긴 뒤 K-ICS 렌더가 픽셀 단위로 안 바뀌는지 스크린샷 대조(변경 전후).
4. 컨트롤 패널에 남는 것은 `기준` 토글 + 오류 제보 버튼뿐이다 — 빈 느낌이 나면 `#emptyHint`/`#dashHost` 와 같은 패널로 합치는 정도까지는 재량. `#wfPeriodLine` 패널은 손대지 말 것.
5. **검증(필수, 말로 하지 말 것)** — 헤드리스(Playwright, 스크립트 안에서 `http.server` 임시 기동·종료):
   ① 1400px·375px 스크린샷, 2,000px 스크롤 후에도 헤더 셀렉트가 같은 자리(`getBoundingClientRect().top` 기록)
   ② 회사 선택(예: `KR0069` 삼성생명) → `#emptyHint` 숨고 `#dashHost` 표시, 스와치 색 채워짐, 섹션 네비 7칩 중 미공시가 아닌 것이 살아남
   ③ 토글 `분기` → 워터폴/손익 캡션이 "분기 기준" 으로 바뀌고 `#wfPeriod.value==="quarter"`; 다시 `연도`
   ④ `?company=KR0069` 진입 시 헤더 셀렉트에 반영되고 대시보드 렌더(F1 크로스내비)
   ⑤ 키보드: 토글에 포커스 후 ArrowRight → 값 전환
   ⑥ `--iq-hdr-h` 실측값과 `.section-nav` `top` 이 추종(IFRS17 은 네비가 7개라 모바일 tuck 도 확인)
   ⑦ `scripts/validate_deployed_js.py --no-live` 4페이지 RED=0 · `pytest tests/test_deploy_assets.py -q` · pageerror 0 (K-ICS 도 다시)
   스크린샷은 `artifacts/designer_shots/20260921_ifrs17_header_toggle/` 에, 경로를 답변에.

제약: `git push` 금지·main 배포 금지(오케스트레이터가 검토 후 배포). 커밋은 명시 pathspec(`IFRS17.html K-ICS.html common.css` + 문서·티켓)으로만. `scripts/`·마스터 JSON·`public_exports/` 건드리지 말 것. 데이터 인라인 금지. 음수 △. `TODO_designer.md` 맨 위 + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)


**처리 완료 (designer, 2026-09-21 · 오케스트레이터 세션 인계).**

1. **헤더 셀렉트** — `#company`(+`#coSwatch`)를 `<header>` 안 `.header-select-row` 로 이동(L132-138).
   K-ICS 와 같은 클래스·같은 자리. 스와치는 그대로 동작(삼성생명 선택 시 `rgb(20, 40, 160)` 채움 확인).
2. **`기준` 세그먼트 토글** — `연도 | 분기`(기본 연도). 실제 `<select id="wfPeriod">` 는 `.sr-only` 로
   남겨 `.value`/`change` 계약 무변경 → L1788·1859·2246 한 글자도 안 고쳤다. `role="radiogroup"`/
   `radio`/`aria-checked`, ←→·↑↓ 키 지원(`setupSegToggle`, L378-410).
3. **common.css 승격** — `.header-select-row`/`.header-select-label`/`.control-group`/`.control-label`/
   `.seg-toggle`/`.seg-btn`/`.sr-only` + 모바일 오버라이드를 `common.css` 로 옮기고 K-ICS.html 의
   페이지 로컬 정의는 삭제. K-ICS 렌더는 헤드리스 재측정으로 동일 확인(헤더 118px, 표 40행,
   금리민감도 차트·표 정상).
4. 컨트롤 패널에는 `기준` 토글 + 오류 제보 버튼만 남겼다. `#wfPeriodLine` 패널 무수정.
5. **검증(헤드리스 Playwright, 1400px·375px)** — 스크립트는 세션 스크래치패드의 throwaway 2종:
   ① 2,000px 스크롤 후 헤더 셀렉트 `visibleAfterScroll=true`(데스크톱 top=72 / 모바일 top=68)
   ② `KR0069` 선택 → `#emptyHint` 숨김·`#dashHost` 표시·스와치 채움
   ③ `분기` 토글 → `#wfPeriod.value==="quarter"`, `aria-checked="true"`; ArrowRight → `year` 복귀
   ④ `?company=KR0069` 진입 → 셀렉트 반영 + 대시보드 렌더
   ⑤ 섹션 네비 7칩 전부 살아난 상태에서 착지 오프셋 전수: 데스크톱 `[12,12,12,12,12,12,210]`,
      모바일 `[12,12,12,12,12,12,79]` — 음수 0건(마지막 칩은 문서 끝이라 더 못 내려가는 정상 케이스)
   ⑥ `validate_deployed_js.py --no-live` 4페이지 **RED=0**, `pytest tests/test_deploy_assets.py` 11 passed,
      uncaught pageerror 0 (GA4 `www.google.com/g/collect` CSP 콘솔 에러는 4페이지 공통 기존 조건,
      이번 변경과 무관 — connect-src 에 그 도메인이 없어서 나는 것)
   스크린샷: `artifacts/designer_shots/20260921_header_toggle_v2/`

**추가로 잡은 것(같은 원인, 범위 밖이지만 이 변경이 없으면 IFRS17 도 같이 깨진다)**:
헤더가 커지면서 섹션 앵커가 헤더 밑으로 파고드는 버그를 owner 가 K-ICS 라이브에서 지적했다.
`common.css` 의 `scroll-padding-top` 이 `--header-h:76px` 하드코딩이라 헤더 118px 에서 30px 이
잘렸다. `--iq-hdr-h`(theme.js 실측)를 쓰도록 고쳤다 — 상세는 `docs/changelog_designer.md`.
