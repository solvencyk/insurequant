---
from: owner
to: designer
created: 20260912T0810Z
status: resolved
route: html
company: JP_MULTI
period: FY2025
track: J-ESR
supersedes: 20260912T0530Z
---

## 미결 (owner) — `jp/index.html` ESR 랭킹을 **루트 `index.html` 모바일 리스트 레이아웃 그대로** + 기준선 색상으로 교체

**owner 2026-09-12 지적(원문 취지).** "한국 insurequant 모바일 화면 레이아웃(막대 리스트)을 그대로 쓰면 되는데 왜 새로 지저분한
ECharts 막대를 만들었나. J-ESR 기준수준 하나 정해서 그보다 높을수록 진한 초록, 낮을수록 진한 빨강으로 칠하는 게 더 직관적이다."
→ ESR 랭킹 섹션의 ECharts 가로막대(`#esrChartLife`/`#esrChartNonlife`, `renderChart()`)를 **버리고**, 루트 `index.html` 의
`.map-list` 리스트(`.li-sector` / `.li-row` / `.li-name` / `.li-bar-track` / `.li-bar` / `.li-val` / `.li-chip` / `.li-more-btn`)를
그대로 옮겨 쓴다. 일본 페이지는 트리맵이 없으므로 이 리스트를 **데스크톱·모바일 모두**에 쓴다(루트는 ≤640px 에서만 리스트).

**정본 참조 (루트 `index.html`, 한 글자도 새로 디자인하지 말 것).**
- CSS: 82~98행 `.map-list`~`.li-chip` 규칙. 그대로 복사해 `jp/index.html` `<style>` 에 넣는다(공유 `common.css` 는 이번엔 건드리지
  않는다 — 라이브 루트 자산). `.map-list{display:none}` 은 jp 에선 `display:block` 으로(항상 표시).
- JS: 877~948행 `renderList()` — 섹터 헤더(`.li-sector`) → 행(`.li-row` = 이름 36% | 바 트랙 | 값) → `FOLD=5` 더보기 버튼(`.li-more-btn`).
  바 폭 = `v / maxV`(섹터별 표시 중인 행의 최대값 기준, 루트와 동일). jp 에서는 더보기를 모바일뿐 아니라 데스크톱에도 적용
  (`isMob` 조건 제거). 섹션 5개 이하면 버튼 없음.
- 색: 544~547행 `colorForRatio()` + 531~543행 `_ratioHsl()` **그대로 복사**(HSL 발산 스케일: 기준 이상 = hue 130 초록, 미만 = hue 0
  빨강, 채도 28→66%·명도 62→24% 로 진해짐). 상수만 일본용으로:
  ```js
  var RATIO_SCALE = { esr: { base: 100, strong: 300 } };
  ```
  `base 100` = 일본 금융청 ESR 감독기준(監督基準 100%, 미달 시 早期是正措置). `strong 300` 은 규제 수치가 아니라 색이 퍼지도록
  잡은 표시용 끝점(현재 13사 분포 p90 ≈ 300, 루트 kics 도 p90 으로 잡음 — 루트 519~526행 주석 그대로 이유). 두 상수 옆에 이
  두 줄 이유를 주석으로 남겨라. 범례에 `監督基準 100%` 를 명시(예: "色: 監督基準100%を上回るほど濃い緑、下回るほど濃い赤").
- 행 클릭 이동은 jp 에 상세 페이지가 없으므로 **넣지 않는다**(`role="link"`·click 핸들러 생략, `title`/`aria-label` 의 요약 텍스트는 유지).

**유지할 것.** ① 정렬 = 직전 티켓의 2단 버킷(`sortBucketed`) 그대로 ② 生保/損保 섹션(reinsurance → 損保) ③ `速報` 는 막대 위 배지
대신 루트의 `.li-chip` 로 이름 옆에 작은 칩("速報") ④ 表·커버리지 도넛·카드는 그대로(도넛만 ECharts 를 계속 쓴다) ⑤ hreflang·CSP·
noindex 그대로. ▲목표수준 마커는 리스트 레이아웃에 자리가 없으니 뺀다(表 備考 에 `目標 190%+` 식으로 텍스트로 남겨도 됨).

**지우는 것.** ECharts 막대 관련 코드 전부(`#esrChartLife/#esrChartNonlife` div·CSS·`renderChart`·`chartInst`·resize 리스너 중 막대분).
ECharts `<script>` 는 도넛이 쓰므로 남긴다. 범례의 業態 색상 항목(파랑/주황)은 이제 의미가 없으니 제거하고 기준선 색 설명으로 교체.

**검증.** 리스트는 순수 HTML/CSS 라 CDN 차단과 무관하게 렌더된다 — 이번엔 막대가 반드시 스크린샷에 보여야 한다. 데스크톱 1280px·
모바일 375px 스크린샷을 같은 파일명(`artifacts/designer/jesr_jp_draft_{desktop,mobile}_20260912.png`)에 덮어쓰기. 색 대비는
`scripts/a11y_contrast_check.py` 로 `.li-val`/`.li-name` 글자 vs 흰 배경만 확인(바 위에 글자 없음). 375px 에서 이름 말줄임·값 정렬 확인.
서브에이전트 생성 금지, 멀티라인 `python -c` 금지, UTF-8 BOM 없음. 끝나면 답변란에 변경 요약·스크린샷 경로, `status: answered`,
`TODO_jp.md`·`docs/changelog_jp.md` 갱신. 보고문에 일본어 문자 금지(회사명은 영문).

## 답변 (designer, 2026-09-12)

`jp/index.html` 의 ESR 랭킹 섹션에서 ECharts 가로막대(`#esrChartLife`/`#esrChartNonlife`, `renderChart()`)를 전부
삭제하고, 루트 `index.html` 의 `.map-list`~`.li-chip`(82~98행) CSS 와 `renderList()`(877~948행), `_ratioHsl`/
`colorForRatio`(531~547행)를 그대로 복사해 `renderList(key)` 로 이식했다. id 만 `esrListLife`/`esrListNonlife` 로
스코프 조정, 색 상수는 `RATIO_SCALE={esr:{base:100,strong:300}}`(base=일본 금융청 감독기준, strong=13사 분포
p90 표시 끝점, 상수 옆 2줄 주석 추가). 데스크톱·모바일 모두 이 리스트를 쓰고(`.map-list{display:block}`), top5+더보기는
데스크톱에도 적용(`isMob` 조건 없음, jp 는 원래도 이 조건이 없었다). 生保/損保 2섹션·top5+더보기·速報 칩(`.li-chip`)·
表·커버리지 도넛은 유지. 行 클릭/`role="link"`/keydown 은 상세 페이지가 없어 넣지 않았고 `title`/`aria-label` 요약
텍스트만 유지, `.li-row` 의 `cursor:pointer`/`:active` 도 클릭이 없어 오탐 어포던스라 판단해 빼는 편차 1건이 있다.
▲目標水準 마커는 表 備考열에 `目標 190%+` 텍스트로 옮겼고(`target_pct`), 業態 색 범례는 감독기준 색 설명으로
교체했다.

검증: `python -m http.server 8896` + Claude Browser preview 로 데스크톱 1280px·모바일 375px 렌더 확인, 콘솔 에러
0건(jsdelivr `ERR_NETWORK_ACCESS_DENIED` 는 이 PC 크로미움 공통 현상으로 도넛에만 영향, 순수 CSS 리스트는 무관하게
정상 렌더 확인). 더보기 클릭 시 生保 9사 전체 펼침 + 表 동시 펼침을 DOM 텍스트로 대조 완료. 색 대비:
`scripts/a11y_contrast_check.py contrast "#212529" "#ffffff"` → 15.43:1(AA 통과, `.li-name`/`.li-val`). 최종
스크린샷은 Playwright 로 재생성해 `artifacts/designer/jesr_jp_draft_desktop_20260912.png`,
`artifacts/designer/jesr_jp_draft_mobile_20260912.png` 에 덮어썼다 — 막대가 실제로 보인다.

`TODO_jp.md` Status (5)·`docs/changelog_jp.md` 2026-09-12 (5) 항목에 상세 기록. Status 최신 5개 유지 원칙에 따라
가장 오래된 (1) 항목은 `docs/todo_archive_jp.md`(신설)로 무수정 이관.

## 종결 재확인 (orchestrator 2026-09-12)

스크린샷(데스크톱 1280·모바일 375) 육안 확인: 루트 모바일 리스트와 동일한 행 구조(이름·速報 칩 | 막대 | 값), 100% 기준
초록 농도(333%↔162% 구분 뚜렷), 生保 top5+더보기·損保 4사, au損害保険 최하단, 범례가 감독기준 설명으로 교체됨.
`jp/index.html` 494행, echarts 막대 잔재 0(`esrChart|renderChart|chartInst` grep 0), CDN 참조 1건 그대로, BOM 없음.
Status 5개 유지로 (1) 항목이 `docs/todo_archive_jp.md` 로 무수정 이관된 것도 확인.

status: **resolved**
