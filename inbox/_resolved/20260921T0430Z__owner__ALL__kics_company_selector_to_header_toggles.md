---
from: owner
to: designer
created: 20260921T0430Z
status: resolved
route: design_change
company: ALL
period: ALL
rule: -
iter: 1
---

## 미결 (sender 작성)

owner 지시(2026-09-21, 원문): "kics.html에서 보험사 선택 부분은 이제 화면 맨 위로 올리고 (스크롤해도 떠있게)
'원보험사별 K-ICS 지급여력비율 변동 추이 / 분기 공시 기준 시계열입니다.' 를 아래 탭 부분으로 넣어야 할거같은데?
그리고 '분기 공시 기준 시계열'도 이젠 꼭 맞는 말도 아니니까 걍 지워라. 기간, 경과조치도 스크롤박스 말고 토글로 바꿔보자."

대상: `K-ICS.html` 하나(공유 `common.css`·`theme.js` 는 필요한 최소만). 지금 구조(HEAD 기준):

- `<header>`(common.css L115, `position:sticky; top:0; z-index:1000`, 항상 떠 있음) 안에 `.brand` + `.header-row`(탭 3개 + 다운로드 CTA).
- `.container` 첫 `.panel`(L130-133)에 `<h2>원보험사별 K-ICS 지급여력비율 변동 추이</h2>` + `<p class="lede">분기 공시 기준 시계열입니다.</p>`.
- `#sec-trend .controls`(L135-190)에 `보험사 선택 <select id="company">`(30 option, value=정식명·label=약칭) · `기간 <select id="period">`(""/quarter/year) · `경과조치 <select id="transition-mode">`(적용전/적용후) · `#reportThisBtn`.
- JS 는 세 컨트롤을 **id 로 `.value` 를 읽는다**: `#company` 8곳(L400·529·983·1046·1284·1363…) · `#period` L401·533·1599-1639(URL 파라미터 `?period=quarter|year` 로 `periodSelect.value` 세팅 + `change` 리스너) · `#transition-mode` L334(`|| '적용전'` 폴백)·L1640. `#company` 는 URL `?company=` 로도 세팅(L1602-1616). `theme.js` 는 헤더 높이를 실측해 `--iq-hdr-h` 로 내려 주고(`hdrH()`·`syncHdrVar()`), 섹션 네비 `top` 과 모바일 tuck(`is-tucked`)이 그 값을 쓴다.

### 시킬 일

1. **보험사 선택을 헤더로.** `#company` 셀렉트를 `<header>` 안(탭 행 또는 그 아래 한 줄)으로 옮겨 **스크롤해도 항상 보이게**. 헤더가 이미 sticky 라 새 sticky 컨테이너를 만들지 말 것. 데스크톱·모바일(375px) 둘 다 헤더가 자연스럽게 커지는 만큼만 커지고, `theme.js` 실측(`--iq-hdr-h`)이 커진 높이를 그대로 받아 섹션 네비 `top`·tuck 이 어긋나지 않는지 확인(지난 라운드 하드코딩 71/88px → 실측 120px 사고 재발 금지). IFRS17.html 의 `#company` 는 이번 범위 밖 — 다만 같은 헤더 패턴을 쓸 수 있게 클래스는 페이지 특정이 아닌 이름으로.
2. **제목 이동 + 부제 삭제.** 첫 `.panel`(h2 + lede)을 없애고, `<h2>원보험사별 K-ICS 지급여력비율 변동 추이</h2>` 는 **`#sec-trend` 패널 상단**(섹션 네비 "지급여력비율 추이" 가 가리키는 자리)으로. `분기 공시 기준 시계열입니다.` 는 **삭제**(다른 곳에 옮기지도, `?` 에 숨기지도 말 것 — owner: "꼭 맞는 말도 아니니까 걍 지워라"). 헤더 `.brand .hint` 의 "K-ICS 지급여력비율 변동 추이" 는 그대로.
3. **기간·경과조치를 토글(segmented control)로.** `<select id="period">` → `분기 | 연도` 2-버튼, `<select id="transition-mode">` → `적용 전 | 적용 후` 2-버튼. `role="radiogroup"` + `role="radio"`/`aria-checked` 또는 `<input type="radio">` 시각적 숨김 중 택일, 키보드(←→·Space) 동작 필수. **JS 계약 유지가 핵심**: 세 곳(L334·L401·L533 등)이 `.value` 를 읽으므로 ① 읽는 쪽을 전부 헬퍼(`getPeriod()`/`getTransitionMode()`)로 갈아끼우거나 ② hidden `<input id="period">` 를 남겨 토글이 그 값을 갱신하고 `change` 를 dispatch 하거나 — 어느 쪽이든 `?period=quarter|year` URL 파라미터 세팅(L1627-1632)과 `change` 리스너(L1639-1640)가 그대로 동작해야 한다. **기간 기본값**: 지금은 "" (미선택 → 표·차트 대신 안내문). 토글은 빈 상태가 어색하니 **기본 `분기`** 로 두되, `canShowTable()` 이 회사만 고르면 바로 그리도록 되는 것을 확인·기록(안내문 "보험사와 조회 기간을 선택해 주세요" 문구도 "보험사를 선택해 주세요" 로). 경과조치 기본은 지금대로 `적용전`.
4. 스타일은 `common.css` 토큰(팔레트 B: `--primary #0f6e68`, 다크 `#54b3aa`)만 쓰고 페이지 인라인 스타일 신설 금지. 선택 상태 대비 WCAG AA, 포커스 링 유지.
5. **검증(필수, 말로 하지 말 것)**: 헤드리스 렌더로 ① 데스크톱 1400px·모바일 375px 스크린샷(헤더에 셀렉트가 있고 2,000px 스크롤 후에도 보이는 것) ② 라이나생명 선택 → 토글 기본 `분기` 로 세부항목 표 41행·차트가 뜨는지 ③ `연도` 토글 → 표가 연도 열로 바뀌는지 ④ `적용 후` 토글 → 값이 바뀌는지(경과조치 적용사 예: 한화생명 2024.4Q 적용전≠적용후) ⑤ `?company=라이나생명보험&period=year` URL 진입이 토글 상태에 반영되는지 ⑥ `scripts/validate_deployed_js.py --no-live` RED=0 ⑦ pageerror 0. 스크린샷을 `artifacts/` 에 남기고 경로를 답변에 적을 것.

제약: `git push` 금지·main 배포 금지(오케스트레이터가 검토 후 배포). 커밋은 명시 pathspec 으로 자기 파일만(같은 트리에서 validation·publishing 에이전트가 동시에 작업 중 — `scripts/`·마스터 JSON·`public_exports/` 건드리지 말 것). 데이터를 HTML 에 인라인하지 말 것. 음수는 △. `TODO_designer.md` 맨 위 + `docs/changelog_designer.md` 갱신.

## 답변 (recipient 작성 — 처리 후)

대상 파일: `K-ICS.html` 하나(모델: Sonnet 5). 커밋 `c130062` 이후 워킹트리(아직 미커밋 상태에서 이 답변 작성 — 아래 커밋에서 확정).

### 1) 보험사 선택 → 헤더

`<header>`(L109-143) 안, 기존 `.header-row`(탭+다운로드) 뒤에 `.header-select-row`(L143-179) 신설 — `#company`
`<select>`(옵션 30개, 원문 그대로 이동, 삭제 아님)를 여기로 옮겼다. `.controls`(구 L172-183)에서는 완전히 뺐다.
`theme.js`의 `hdrH()`/`syncHdrVar()`는 `header.getBoundingClientRect().height`를 그대로 실측하므로(하드코딩 없음),
행이 하나 늘어난 새 헤더 높이가 자동으로 `--iq-hdr-h`에 반영되고 `.section-nav`의 `top`·tuck이 그대로 맞는다 —
지난 라운드(71/88px 하드코딩 → 120px 사고) 재발 없음. 실측: 데스크톱 1400px·모바일 375px 둘 다 2000px 스크롤
후에도 `#company`가 `getBoundingClientRect().top`이 뷰포트 안(≥0, <innerHeight)에 남아 있음
(`artifacts/designer_shots/20260921_header_toggles/{desktop_1400,mobile_375}_scrolled.png`).
클래스명은 `header-select-row`/`header-select-label`로 K-ICS 전용이 아니게 지었다(IFRS17.html이 나중에
같은 패턴을 쓸 수 있게) — 공통 규칙(≥3페이지 byte-identical만 hoist)에 따라 지금은 common.css로 옮기지
않고 K-ICS.html 로컬 `<style>`에 둔다.

### 2) 제목 이동 + 부제 삭제

첫 `.panel`(구 h2+lede)을 삭제하고 `<h2>원보험사별 K-ICS 지급여력비율 변동 추이</h2>`를 `#sec-trend`
패널 최상단(L192)으로 옮겼다. `분기 공시 기준 시계열입니다.`(`<p class="lede">`)는 완전히 삭제 — 다른 곳으로
옮기지도, `?` 툴팁에 넣지도 않았다(owner: "꼭 맞는 말도 아니니까 걍 지워라" 그대로). 헤더 `.brand .hint`의
"K-ICS 지급여력비율 변동 추이"는 무변경.

### 3) 기간·경과조치 → 세그먼트 토글

`<select id="period">`/`<select id="transition-mode">`는 **DOM에 그대로 남기고** `.sr-only`(L143 부근에 정의,
index.html과 동일한 clip-rect 패턴)로 화면에서만 숨겼다(`tabindex="-1" aria-hidden="true"`) — `.value`를 읽는
기존 JS 8곳 이상(`getTransitionMode` L357-359, `getFilteredData` L401/533 부근, URL 파라미터 세팅
L1684-1690, `change` 리스너 L1706-1707 등)은 **한 글자도 안 고쳤다**. 대신 보이는 UI는
`role="radiogroup"`(L195/206) + `<button role="radio" aria-checked>` 2개(`.seg-toggle`/`.seg-btn`,
L196-197·207-208)이고, 새 헬퍼 `setupSegToggle()`(L366-395)이 클릭·키보드(←→) 시
`selectEl.value = ...; selectEl.dispatchEvent(new Event('change'))`를 실행해 기존 `change` 리스너가
그대로 `updateTable()`을 태운다. `<button>` 네이티브라 Space/Enter는 기본 클릭으로 동작, ArrowLeft/Right는
로빙 탭인덱스(활성 버튼만 `tabindex=0`)로 포커스 이동+즉시 적용(APG radiogroup 패턴). 초기화는
L1696-1699(`periodToggle`/`transitionToggle` 생성 후 `.sync()` — URL 파라미터로 `.value`가 직접 바뀐
케이스를 토글 UI에 반영).

**기간 기본값 = 분기**(L200 `<option value="quarter" selected>`, 토글 버튼 기본 active도 `quarter`) —
`canShowTable()`(구현 무변경, `company && period`)이 이제 항상 `period`를 갖고 있으므로 회사만 고르면
바로 렌더된다(실측 아래). 안내문 "보험사와 조회 기간을 선택해 주세요" → "**보험사를 선택해 주세요**"
(L217-218, 부제도 "헤더의 드롭다운 메뉴에서 보험사를 선택하면..."으로 갱신 — 셀렉트가 실제로 헤더로
옮겨갔으므로). 경과조치 기본은 그대로 `적용전`.

색은 팔레트 B 토큰만: `.seg-btn.active{background:var(--primary);color:var(--on-primary)}` — `.tab.active`와
같은 조합(기존 검증됨). `.seg-btn:focus-visible{outline:2px solid var(--primary);outline-offset:-2px}`인데
active 버튼은 배경 자체가 `--primary`라 같은 색 링이 안 보이는 문제를 발견해 `.seg-btn.active:focus-visible{
outline-color:var(--on-primary)}`로 추가 수정(a11y-audit 스킬 절차대로 실측 후 즉시 수정 — 기존 렌더값을
바꾸는 게 아니라 신설 컴포넌트의 포커스 링 가시성이라 owner 승인 없이 바로 고쳤다). 대비 실측
(`scripts/a11y_contrast_check.py`): 라이트 `#fff`/`#0f6e68` 6.09:1, 다크 `#0c110f`/`#54b3aa` 7.62:1
(WCAG AA 텍스트 4.5:1·UI 경계 3:1 모두 통과), 비활성 버튼 텍스트 `#212529`/`#fff` 15.43:1, 라벨
`--muted`/`#fff` 4.69:1.

### 검증 (7항목, 헤드리스 Playwright — `scripts/_probes/_20260921_verify_header_toggles.py`, 미커밋 throwaway,
로컬 `http.server` 랜덤 포트 + venv playwright, 재현: `PYTHONIOENCODING=utf-8
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/_20260921_verify_header_toggles.py`)

1. **스크린샷 + 스크롤 후 노출**: 데스크톱 1400px·모바일 375px 둘 다 `true`
   (`artifacts/designer_shots/20260921_header_toggles/{desktop_1400,mobile_375}_{top,scrolled}.png`).
2. **라이나생명 선택 → 기본 분기 토글로 표+차트**: `period.value="quarter"`, tbody 40행, `#chart` visible=true
   (`2_lina_default_quarter.png`).
3. **연도 토글 → 표 연도 열**: `period.value="year"`, 헤더 `["항목명","2023.4Q","2024.4Q","2025.4Q","2026.2Q"]`
   (`3_lina_year_toggle.png`).
4. **적용후 토글 → 값 변경**(한화생명 2024.4Q): `transition-mode.value="적용후"`, 적용전/적용후 표 텍스트
   `pre_vs_post_differ=true` (`4_hanwha_life_post_toggle.png`).
5. **URL `?company=라이나생명보험&period=year` 진입 → 토글 상태 반영**: `#company.value="라이나생명보험"`,
   `#period.value="year"`, `연도` 버튼 `active`+`aria-checked="true"` (`5_url_param_year.png`).
6. **`validate_deployed_js.py --no-live` RED=0**: 실행 결과 `RED=0 (clear)`
   (K-ICS.html 스크립트 7/7·바인딩 566·참조지점 769, 4페이지 전부 RED=0).
7. **pageerror 0**: Playwright `console`(error) + `pageerror` 리스너 누적 0건(모든 페이지/시나리오 합산).

추가(보너스, 키보드 명시 확인): `#period-toggle`의 active 버튼에 포커스 후 `ArrowRight` →
`period.value="year"`+활성 라벨 "연도", `ArrowLeft` → 다시 `"quarter"`.

`pytest tests/test_deploy_assets.py -q` → **11 passed**(재인라인 금지·BOM·keep-list 전부 그대로 통과).

### 못한 것 / 발견한 별개 이슈

발견(범위 밖, spawn_task로 별도 티켓 `task_1dc9b489` 발주): 모바일 375px에서 `기타공시` 탭이
`⬇ 테이블 다운로드(.xlsx)` 버튼에 가려 겹치는 기존 버그를 발견했다 — **이번 변경이 원인이 아님**을
HEAD 버전(변경 전)을 임시 디렉터리에 체크아웃해 같은 뷰포트로 재현해 확인했다(`common.css`의
`.header-row`/`.tabs`/`.download-cta`가 원인, 4페이지 공유라 범위가 커서 이 티켓에서 같이 고치지
않았다). `common.css`는 이번 티켓에서 전혀 건드리지 않았다(변경분 = `K-ICS.html` 단독).

나머지 5항목은 지시대로 전부 구현했다.


## 종결 (orchestrator, 2026-09-21)

독립 헤드리스 재확인(HEAD 3573509, 1400px·375px): 회사만 선택 → 기본 분기·적용전으로 세부항목 표 41행·차트·민감도 7행 렌더 / 연도 토글 → 열이 2023.4Q·2024.4Q·2025.4Q·2026.2Q 로 전환 / 경과조치 토글 ArrowRight → hidden select 값 적용후 동기화 / 2,500px 스크롤 후에도 헤더 셀렉트 top 72px(모바일 68px) 고정 / `--iq-hdr-h` 실측 118px(모바일 110px), 섹션 네비 top 130px(=118+12) 추종 / `?company=한화생명&period=year` 진입 시 토글·회사 반영 / "분기 공시 기준 시계열" 문자열 0 / pageerror 0 / `validate_deployed_js.py --no-live` RED=0 / `test_deploy_assets` 11 passed. 범위 밖 발견(모바일 375px 기타공시 탭이 다운로드 버튼에 가림, 변경 전부터)은 별도 작업으로 분리됨.
