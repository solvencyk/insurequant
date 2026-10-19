---
from: orchestrator
to: designer
created: 20261019T1400Z
status: open
route: fix
company: ALL
period: ALL
lane: "-"
iter: 1
---

## 미결 (sender 작성)

`compare.html` · `privacy.html` 접근성 감사(2026-10-19, WCAG 2.1 AA)에서 나온 위반 18건이다. 측정 방법·조건·통과 항목·전체 표는 `docs/a11y_baseline.md` §5 가 정본이고, 여기는 고칠 일과 수락 기준만 적는다. 감사 때는 아무것도 고치지 않았다.

처리 순서와 승인:
- **바로 고쳐도 되는 것(값이 안 바뀌는 추가·동작 수정)**: C1 · C2 · C6 · C8 ~ C17. `common.css`·`theme.js` 변경이면 6페이지 전부 영향이므로 고친 뒤 `index`·`K-ICS`·`IFRS17`·`공시보고서` 도 1280/375 로 열어 깨짐이 없는지 확인한다.
- **owner 승인 뒤에만 고치는 것(화면 색·토큰 값이 바뀜, `docs/a11y_baseline.md` §2b 규칙)**: C3 · C4 · C5 · C7 · C18. 승인 전에는 이 티켓에 값 제안만 남기고 코드는 건드리지 않는다.
- **owner 결정(2026-10-19 구두, 「접근성 추천대로」)**: 이번 범위는 **C1 · C2 · C3 · C4 · C6** 다섯 건이다. C3 · C4 는 승인됨(검색창 테두리·다크 placeholder 만, 차트 색은 그대로). **C5 · C7 · C18 은 하지 않는다**(수치가 같이 표시돼 정보가 중복). C8 ~ C17 은 이번 범위 밖이라 열어 둔다.
- 수정 뒤 재측정용 검사 스크립트 `scripts/check_a11y_compare_privacy.py` 를 `scripts/check_notice_popup.py` 패턴(빈 포트 로컬 서버, `?iq_internal=1`, GA·수집기 요청 route 차단, 브라우저 없으면 SKIP=「안 돌렸다」 보고)으로 만든다. 아래 수락 기준의 수치를 그대로 단언한다.
- 모든 검증은 1280 · 375 x 라이트 · 다크, compare 는 생보 4사(삼성생명·한화생명·교보생명·신한라이프)·손보 4사(삼성화재·DB손보·현대해상·KB손보)·회사 미선택 3 시나리오로 돈다.

### C1 (중간) `?` 팝오버가 마우스로 닿지 않는다 — `common.css` `.iq-help-pop` (공통)
버튼 하단과 팝오버 상단 사이 6px 틈에서 `:hover` 가 풀려 팝오버가 `pointer-events:none` 이 된다(1px 단위 이동: y=315 불투명도 0.84, y=323 0). 제안: 팝오버에 `::before` 다리(`top:-8px;height:8px`)를 둔다.
- 수락 기준: 마우스를 `?` 버튼 중앙에서 팝오버 중앙까지 1px 단위로 옮기는 동안 팝오버 `opacity` 가 내내 1. 키보드 포커스·Esc 닫기·375 폭 위치(`[8,348]`)는 그대로.

### C2 (중간) 칩 제거·회사 추가 뒤 포커스가 `body` 로 사라진다 — `compare.html`
칩 제거 버튼에서 Enter 하면 `document.activeElement` 가 `body`. 4번째 회사를 키보드로 추가해도 입력창이 비활성되며 `body`. 제안: 제거 뒤 다음(없으면 이전) 칩의 제거 버튼, 칩이 없으면 검색창으로 `focus()`. 4곳이 차면 첫 칩 제거 버튼으로.
- 수락 기준: 두 경우 모두 조작 직후 `activeElement` 가 `body` 가 아니고 화면에 보이는 컨트롤. 안내문(`#live`)은 그대로 나온다.

### C3 (중간·owner 승인) 입력창 테두리 대비 — `--border` 를 쓰는 폼 컨트롤 (공통)
검색창 테두리 `#e4e4e2` on `#fff` 1.27:1, 다크 `#313431` on `#151615` 1.44:1(기준 3:1). 제안: 새 토큰 `--control-border`(라이트 `#85888d` 3.56:1, 다크 `#727772` 3.97:1)를 만들어 입력창·체크박스에만 쓴다. `--border` 값은 그대로.
- 수락 기준: `input#addco` 테두리 대비 라이트·다크 모두 3.0:1 이상(계산 스크립트로 단언). owner 승인 기록이 이 티켓 `## 답변` 에 있어야 한다.

### C4 (중간·owner 승인) 다크 모드 placeholder — 공통 입력창
UA 기본 `#757575` on `#151615` 3.94:1(라이트 4.61:1). 제안: `input::placeholder{color:var(--muted)}`(라이트 5.76, 다크 6.83).
- 수락 기준: 회사 미선택 화면 `input#addco::placeholder` 대비 라이트·다크 모두 4.5:1 이상.

### C5 (중간·owner 승인) 유지율 묶음 막대 팔레트 — `compare.html` `PAL_BAR`
라이트에서 흰 배경 대비 `#8ccfc6` 1.77 · `#f6b49f` 1.76 · `#a8c1f0` 1.82 · `#e6d27e` 1.51:1. 색각 쌍 `#f6b49f`/`#e6d27e` ΔRGB 12·9, `#8ccfc6`/`#a8c1f0` 31·30. 제안: 막대에 어두운 윤곽(`#4a9d92` · `#d9764f` · `#6f94d6` · `#a38d1f`, 각 3.05~3.29:1, `borderWidth` 1.5) 또는 팔레트를 어둡게.
- 수락 기준: 라이트·다크에서 막대 테두리 또는 채움색의 배경 대비 3:1 이상, 같은 묶음 안 색 쌍의 protan·deutan ΔRGB 가 60 이상이거나 막대 윤곽·수치 라벨 등 색 밖 단서가 남아 있다.

### C6 (중간) 좁은 화면 손해율 꺾은선이 색으로만 구분된다 — `compare.html` SVG(`lossMobile`)
선이 모두 실선에 마커·직접 라벨이 없다. 손보 4사에서 현대해상 `#ea690c` / KB손보 `#b88700` ΔRGB 40·49(다크 `#F47920`/`#FFBC00` 48·47). 제안: 넓은 화면 `PT`(원·삼각·사각·마름모)와 같은 마커를 선에 달고 현재가치 표 견본에도 같은 모양을 쓴다.
- 수락 기준: 375 폭 손해율 카드에서 선마다 서로 다른 마커 모양이 있고 표 견본과 모양이 같다. 색은 안 바뀐다.

### C7 (낮음·owner 승인) 손해율 선 폴백 팔레트 대비 — `compare.html` `PAL_LINE`/`lcShown`
`visibleOn` 이 키컬러에만 적용돼 폴백 색이 라이트에서 `#4fb0a5` 2.60 · `#ee8f72` 2.38 · `#7b9fe6` 2.64 · `#cdb04a` 2.12:1. 제안: `lcShown` 이 폴백 색에도 `visibleOn` 적용(예: `#3a9a8f` 3.39 · `#e0693f` 3.35 · `#5f87dd` 3.50 · `#a68a1c` 3.35).
- 수락 기준: 라이트·다크 모두 `Chart.instances` 의 모든 선 `borderColor` 가 배경 대비 3.0:1 이상(생보 4사·손보 4사).

### C8 (낮음) 카드 제목 접근 이름에 설명이 붙는다 — `compare.html` 카드 `h3`
`h3` 안의 `?` 버튼·`role=tooltip` 때문에 제목 이름이 56~585자(손해율 카드 585자).
- 수락 기준: 모든 카드 `h3` 의 접근 이름이 제목 + 단위 글자만(60자 이하), `?` 버튼과 설명은 그대로 동작(`aria-describedby` 유지).

### C9 (낮음) 섹션 공유 버튼 이름 중복 — `theme.js` `mountSectionShare` (공통)
compare 10개가 모두 `aria-label` 「이 섹션 스크린샷 공유」.
- 수락 기준: 한 페이지의 섹션 공유 버튼 `aria-label` 이 서로 다르고 섹션 이름을 포함한다(예: 「지급여력비율 스크린샷 공유」).

### C10 (낮음) `<main>` · 건너뛰기 링크 없음 — `compare.html` · `privacy.html`
compare 데스크톱에서 첫 카드 컨트롤까지 Tab 38번, privacy 본문 첫 링크까지 8번.
- 수락 기준: 본문 컨테이너가 `<main>`, 첫 Tab 에 「본문으로 건너뛰기」 링크가 보이고 Enter 로 본문에 포커스. compare 데스크톱 첫 카드 컨트롤까지 Tab 15번 이하(가이드 빼기 버튼 `tabindex="-1"` 등, Delete 키 동작은 유지).

### C11 (낮음) 감소 모션 — `compare.html` Chart.js · `theme.js` `scrollBy`
`prefers-reduced-motion` 에서도 `Chart.defaults.animation.duration` 1000(차트 2개). `theme.js` 의 `scrollBy({behavior:'smooth'})`(터치 `?` 팝오버 보정)는 reduce 판정이 없다.
- 수락 기준: reduced-motion 맥락에서 Chart.js 차트 `options.animation` 이 `false`(또는 duration 0), `scrollBy` 가 `auto`.

### C12 (낮음) 경과조치 토글·중앙값 체크박스 상태 안내 없음 — `compare.html`
두 조작 뒤 `#live` 텍스트가 직전 값 그대로.
- 수락 기준: 두 조작 직후 `#live` 에 바뀐 상태 문구(예: 「경과조치 적용 전」 · 「같은 유형 업계 중앙값 표시」)가 들어간다.

### C13 (낮음) 테마 토글 `aria-pressed` + 바뀌는 레이블 — `theme.js` (공통)
「다크 모드로 전환」(pressed=false) → 「라이트 모드로 전환」(pressed=true).
- 수락 기준: 레이블이 상태에 따라 바뀌거나 `aria-pressed` 가 있거나 둘 중 하나만(둘 다 아님).

### C14 (낮음) 넓은 화면 손해율 꺾은선의 텍스트 대안 — `compare.html`
`canvas` `aria-label` 이 선마다 시작값→끝값만 담는다. 좁은 화면은 현재가치 표가 있다.
- 수락 기준: 넓은 화면에서도 선별 현재가치 표(또는 `<details>`)가 DOM 에 있어 스크린리더로 읽힌다.

### C15 (낮음) 가로 스크롤 표 영역 이름 없음 — `privacy.html` `.policy-table-wrap`
- 수락 기준: 375 폭에서 이 영역이 `role="region"` + `aria-label` + `tabindex="0"` 이고 포커스 링이 보인다.

### C16 (참고) 터치 대상 크기 — `?` 버튼 22x22 · 체크박스 18x18 · 레일 빼기 22x22 · 375 폭 브랜드 링크 높이 19px (공통)
WCAG 2.1 AA 요건은 아니다(2.2 의 2.5.8). 2.2 AA 를 목표로 삼는다면 24px 이상으로. 수락 기준은 owner 가 목표 버전을 정한 뒤에 적는다.

### C17 (참고) 제목 단계 — compare `h1` 다음 `h3` · privacy `h1` 둘
- 수락 기준: compare 카드 제목이 `h2`(또는 문서 구조 안에서 건너뜀 없음). privacy 두 번째 `h1` 은 유지해도 된다.

### C18 (참고·owner 승인) 비앵커 막대 대비 — `compare.html` `.brow:not(.anchor) .bar{opacity:.65}`
라이트 `#9a9c9f` on `#fff` 2.75:1(다크 3.61). 막대마다 수치가 있어 정보는 중복. 제안: 불투명도 .8 쯤.
- 수락 기준: 라이트·다크 모두 막대색 합성값의 배경 대비 3.0:1 이상.

## 답변 (recipient 작성 — 처리 후)
**2026-10-19 designer 처리: C1 · C2 · C3 · C4 · C6 완료(로컬, 미배포·미푸시). 이 티켓은 C8~C17 이 열려 있어 `status` 는 그대로 둔다.**

owner 승인 기록(C3 · C4 요건): 2026-10-19 구두 결정 「접근성 추천대로」 — 이번 범위는 C1·C2·C3·C4·C6 다섯 건. C3 · C4 색 변경은 승인됨(글자 입력창 테두리와 placeholder 만, 차트 색은 그대로). C5 · C7 · C18 은 하지 않는다(수치가 함께 표시돼 정보가 겹침). 이 세션에서 C5 · C7 · C18 코드는 건드리지 않았고(`PAL_BAR`·`PAL_LINE` 원문 일치를 검사 스크립트가 단언), C8~C17 은 범위 밖이라 그대로 열려 있다.

**고친 것**
- C1 `common.css` · `theme.js`: ① `.iq-help-pop::before` 다리(6px 틈, `--up` 이면 아래쪽). ② 마우스 유예 - `.iq-help` 를 떠난 뒤 400ms 동안 `is-grace` 클래스로 팝오버를 유지한다(`theme.js` `pointerleave`/`pointerenter`, 터치 제외; `common.css` `.iq-help.is-grace > .iq-help-pop`, Esc 로 닫은 상태 우선). 버튼 옆면으로 나가 팝오버로 비스듬히 가는 경로에서 `:hover` 가 틈에서 풀려도 팝오버가 남는다. 먼저 시도한 버튼 옆 삼각형 호버 영역은 화면 오른쪽 끝 `?` 에서 호버 중 문서를 가로로 넓혀(375 폭 `index` +89px · `K-ICS` +92px) 독립 검증자가 잡았고, 이 방식으로 바꿨다. 키보드 포커스로 열림·Esc 닫힘·375 폭 위치(좌우 여백 8px, 측정 [7.6,363])는 그대로.
- C2 `compare.html`: 칩 제거 뒤 같은 자리에 온 다음 칩(없으면 이전 칩)의 제거 버튼, 칩이 없으면 검색창. 4곳째를 키보드로 더하면 첫 칩의 제거 버튼. `#live` 문구(「OO 제거」 · 「OO 추가」)는 그대로 나온다. 마우스·터치로 마지막 칩을 뺄 때는 화면 키보드·추천 목록이 뜨지 않게 검색창으로 옮기지 않는다(`click` 의 `detail===0` 일 때만 검색창).
- C3 `common.css` 새 토큰 `--control-border`(라이트 `#85888d` · 다크 `#727772`), `--border` 값은 그대로. 적용: `input#addco`(compare 페이지 css), `.iq-input` · `.iq-textarea`(오류 제보·내려받기 설문 창). 선택 상자(`select`)는 owner 범위(글자 입력창·체크박스) 밖이라 안 바꿨다. 체크박스는 브라우저 기본 표시라 테두리를 칠할 수 없고, 실측이 이미 라이트 4.54:1 · 다크 4.92:1 이라 토큰을 적용하지 않았다.
- C4 `common.css`: `input::placeholder, textarea::placeholder{color:var(--muted);opacity:1}`(Firefox 기본 .54 도 고정).
- C6 `compare.html` 375 폭 SVG: 선마다 넓은 화면 `PT`(원 · 삼각 · 사각 · 마름모, 선택 순서) 와 같은 모양·크기(반지름 4)의 표식을 8차년마다 하나씩(선마다 2차년 어긋나게) 찍고, 현재가치 표 견본에도 같은 모양. 선 색은 그대로(넓은 화면 `Chart.js` 색과 같은지 단언). 흐린 점선 구간(위험보험료 100억원 미만)의 표식은 넓은 화면처럼 속 빈 표식(배경색 채움 · 흐린 윤곽 2px)이고 흐린 구간마다 표식이 하나 이상 있다. 단위 선택기의 n/a 문구는 건드리지 않았다.
- 덤으로 고친 기존 버그 1건(`theme.js` 에 `IQTheme.clampHelpPops` 노출 1줄 + `compare.html` `flipHelp` 1줄): 375 폭 손해율 카드의 `?` 팝오버가 키보드 포커스·탭에서 화면 왼쪽 밖(`[-291,49]`)에 남았다. `theme.js` 의 화면 안 보정이 `compare.html` 의 방향 전환보다 먼저 돌아 낡은 위치가 남던 것이고, 검사 스크립트가 옛 판(HEAD)에서도 같은 값으로 잡았다. 이제 `[8,348]`.

**측정(`scripts/check_a11y_compare_privacy.py`, 3357개 단언, 실패 0)**
- 1280 · 375 x 라이트 · 다크, compare 3 시나리오(생보 4사 · 손보 4사 · 회사 미선택) + 공통 css 를 쓰는 5개 페이지 전부.
- C3: 검색창 테두리 최소 라이트 3.56:1 · 다크 3.97:1(옛 판 1.27 · 1.44), 오류 제보 창 입력창도 같은 값. C4: placeholder 최소 라이트 5.76:1 · 다크 6.83:1(옛 판 다크 3.94). `--border` 값 변동 0.
- C1: 마우스 경로(수직 우선 · 직선 · 아래로 휜 곡선) 버튼 39개 전부 통과(옆으로 먼저 멀리 가는 곡선은 400ms 를 넘으면 풀려 참고만), 다리·유예를 끈 음성 대조에서는 풀려 시험이 실패한다. 호버 중 가로 넘침: `?` 버튼 115개 전수(1280 · 375 마우스, 라이트 · 다크)에서 `scrollWidth` − 화면 폭 = 0. 한계: 탭 뒤에 남는 `:hover` 는 Playwright 터치 에뮬레이션이 만들지 못해(탭해도 `:hover` 불일치) 실기기로는 못 쟀고 375 폭 마우스 호버로 대신 쟀다. C2: 제거 4단계(가운데 · 마지막 · 첫째 · 하나 남은 칩)와 4곳 추가 전부 `activeElement` 가 보이는 컨트롤이고 `#live` 문구 일치. C6: 단위 선택 전 옵션 순회 중 흐린 구간이 나온 8건 포함 선마다 서로 다른 모양 · 표 견본과 같은 모양 · 넓은 화면 `pointStyle`·색과 일치.
- 변이시험: 옛 판 `compare.html` · `common.css` 를 겹쳐 서빙하면 311건이 실패한다(C1 다리 · C2 포커스 body · C3 1.27 · C4 3.94 · C6 표식 0 · 토큰). 즉 검사가 실제로 버그를 잡는다. 이 311건은 마우스 유예·호버 넘침 시험을 넣기 전의 검사 스크립트로 잰 값이라 그 뒤 판으로는 다시 안 쟀다.
- 요청 전송: 수집기·분석 비콘 0건. 페이지에 정적으로 박힌 gtag 스크립트 요청 53건은 route 로 전부 중단(전송 0). 콘솔 오류 0.
- 화면 확인: 6페이지 x 1280/375 x 라이트/다크 24장을 옛 판 css 와 픽셀 비교 — 차이는 compare 검색창(테두리 · placeholder 칸)뿐이고 index · K-ICS 의 소수 픽셀 차이는 숫자 애니메이션 글자 가장자리 잡음이다. 레이아웃 깨짐 없음. 스크린샷은 `artifacts/designer/a11y_compare_privacy/`(미추적).
- 재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_a11y_compare_privacy.py` (종료코드 0 = 통과, 브라우저가 없으면 SKIP 을 「안 돌렸다」로 인쇄). `pytest tests/test_deploy_assets.py tests/test_push_gate_wiring.py -q` → 78 passed, 1 skipped.

**남은 것 · 알림**
- C8 ~ C17 열림(범위 밖). C5 · C7 · C18 owner 거절.
- 검사에서 마우스 시험을 건너뛴 것은 K-ICS 의 닫힌 패널 안 `?` 버튼 2개뿐(보이지 않음).
- compare 데스크톱 첫 화면에서 맨 위 제목 「사별 비교」 윗부분이 고정 검색줄 밑에 걸린다(옛 판에서도 동일, 이번 변경과 무관). 필요하면 별도 티켓.
- `docs/a11y_baseline.md` §5e 에 처리 현황을 적었다.
