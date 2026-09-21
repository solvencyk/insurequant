---
from: owner
to: designer
created: 20260921T0430Z
status: open
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

