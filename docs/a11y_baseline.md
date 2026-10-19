# A11y baseline + audit (2026-07-21)

> Ordered by [inbox/designer/20260721T0233Z](../inbox/_resolved/20260721T0233Z__owner__MULTI__adopt_a11y_audit_baseline.md) (`ui-ux-pro-max` external skill reviewed and passed on — see §4). Scope: baseline definition + audit + owner-review queue for the 4 deployed pages (`index.html`, `K-ICS.html`, `IFRS17.html`, `공시보고서.html`). **Owner-review queue sign-off received same day (2026-07-21) — all color/contrast items fixed, see §2b.** **Since 2026-10-19 the scope is all 6 deployed pages (`index`, `K-ICS`, `IFRS17`, `공시보고서`, `compare`, `privacy`): `compare.html` and `privacy.html` were first audited on that date, see §5.**

## 1. Target level

**WCAG 2.1 AA**, scoped to what actually applies to a data-dashboard site (no audio/video, no complex forms beyond `<select>`/`<input>`):

| Criterion | Rule | Threshold |
|---|---|---|
| 1.4.3 Contrast (text) | normal text | ≥ 4.5:1 vs its background |
| 1.4.3 Contrast (text) | large text (≥24px, or ≥19px bold) | ≥ 3:1 |
| 1.4.11 Non-text contrast | UI component boundaries/icons that carry meaning | ≥ 3:1 |
| 1.4.1 Use of color | never color-only for meaning | secondary cue required (symbol/label/position) |
| 2.1.1 Keyboard | every interactive control | reachable + operable via keyboard alone |
| 2.4.7 Focus visible | every focusable control | visible focus indicator |
| 3.3.2 Labels | every form control | programmatically associated label |
| — colorblindness | categorical/diverging chart palettes | pairs used together should stay distinguishable under protanopia/deuteranopia simulation (not a WCAG SC by number, but load-bearing for a financial dashboard where red/green carries meaning) |

Method for contrast: standard WCAG relative-luminance formula, computed with a small Python script (`scripts/a11y_contrast_check.py`, added alongside this doc — see §4) rather than eyeballed, since hand-computed contrast ratios are easy to get wrong. Method for colorblindness: linear-RGB matrix simulation (Brettel/Viénot-style protanopia/deuteranopia approximation) on the actual color literals in each file, flagging pairs whose simulated Euclidean RGB distance drops sharply from the unsimulated distance.

## 2. Audit results

### 2a. Fixed now (low-risk, purely additive — no rendered-value change, per the order's "명백한 저위험 위반은 바로 고쳐도 됨")

All of these add capability/visibility without changing anything an existing mouse user sees, so they don't touch the owner-gated token values in `common.css`.

| # | File | Issue | Fix |
|---|---|---|---|
| 1 | `index.html` | Treemap cells (`.cell`) — the site's primary click-to-navigate interaction — had a click listener only, no keyboard path at all (WCAG 2.1.1 fail) | Added `tabindex="0"`, `role="link"`, `aria-label` (reusing the existing `title` text), and a `keydown` handler for Enter/Space that calls the same navigation function as click |
| 2 | `index.html` | Mobile list rows (`.li-row`, the ≤640px fallback for the same navigation) — same click-only gap | Same fix as #1 |
| 3 | `index.html` | Custom toggle switch (`.toggle-input{opacity:0;width:0;height:0}`) — real focus lands on a 0×0 invisible checkbox, so the sitewide `:focus-visible` ring is effectively invisible to keyboard users (WCAG 2.4.7 fail) | Added `.toggle-input:focus-visible + .toggle-label{outline:2px solid var(--primary);outline-offset:2px}` so the visible label gets the ring |
| 4 | `공시보고서.html` | Doesn't link `common.css` at all (only 3 of the 4 pages did) — so this page has **no** `:focus-visible` ring and **no** `prefers-reduced-motion` handling sitewide baseline | Added `<link rel="stylesheet" href="common.css"/>` in the same position as the other 3 pages (before the page's own inline `<style>`, per the extraction contract) |
| 5 | `K-ICS.html`, `IFRS17.html`, `index.html` | Every chart `<canvas>`/ECharts `<div>` (10 total: K-ICS main/donut×2/sensitivity/forward; IFRS17 waterfall/history/amort/PL/NB; index treemap/bubble) had no `role`/`aria-label` — screen reader users get nothing | Added `role="img"` (or `role="group"` for the treemap, since its children are now individually focusable links — an `img` can't semantically contain link children) + a concise Korean `aria-label` per chart |
| 6 | `K-ICS.html`, `IFRS17.html`, `공시보고서.html` | Active tab link (`.tab.active`) had no `aria-current` — screen readers can't tell which page is current beyond the (also color-only) visual highlight | Added `aria-current="page"` alongside the existing `active` class. `index.html`'s own tab bar doesn't list itself, so no change needed there. |

Verified via Claude Browser preview: 0 console errors on all 4 pages; a dispatched `Enter` keydown on a treemap cell navigated to `K-ICS.html?company=...` exactly like a click; `공시보고서.html` now loads `common.css` and has the `:focus-visible` rule; mobile (375px) list rows carry the same `tabindex`/`role`/`aria-label`.

### 2b. Owner-review queue — resolved 2026-07-21 (owner: "do it now")

Rows 7–9, 11, 13 below were fixed in the same session, verified with `scripts/a11y_contrast_check.py` before editing (not eyeballed). Row 12 was fixed the same way, then **reverted the next day per owner** (2026-07-22) — see its row for why. Row 10 needed no change (already compliant) and row 14 remains open (content-authoring task, different category — see below).

| # | File | Finding | Fix applied |
|---|---|---|---|
| 7 | `common.css` `--muted` | `#6c757d` on `--card` = 4.45:1 | → `#6a737a` (4.83:1 on white, 4.58:1 on `--card`) |
| 8 | `index.html` bubble-legend | `● 손해` label `#16a34a` on white = 3.30:1 | → `#15803d` (5.02:1). `SECTOR_COLOR['Non-Life']` (the actual bubble dot fill) left unchanged — that's a graphic element under the 3:1 UI threshold, already compliant; only the text label needed darkening |
| 9 | `K-ICS.html` donut center / `IFRS17.html` missing-data cells | `#adb5bd` "no data" placeholder on white = 2.07:1 | → `#6a737a` (same value as fixed `--muted`, for consistency) in both files |
| 10 | `K-ICS.html` teal/pink series pair | Simulated under protanopia/deuteranopia: stays distinguishable (ΔRGB 113–143) | No change needed — already compliant |
| 11 | `IFRS17.html` `NB_LINE_COLORS` 6-color categorical palette | orange↔red ΔRGB 51/52, purple↔teal ΔRGB 39 under deuteranopia/protanopia | → `["#0d6efd","#009E73","#D55E00","#343a40","#CC79A7","#7c5c00"]`. Tried a minimal 2-color swap first — kept re-clashing elsewhere in the 6-set (colorblind confusability isn't decomposable pairwise). Full-palette search (varying hue AND lightness, one near-neutral gray slot) found a set whose **global worst pair is ΔRGB 82** (was 39) across both protanopia and deuteranopia, all 6 colors ≥3:1 contrast on white |
| 12 | `index.html` treemap swatch + `colorForRatio()` (the live per-cell color function) — red↔green diverging scale | Endpoint contrast drops to ~1.1–1.3:1 under simulation — classic red-green diverging problem | **Reverted 2026-07-22.** Tried below-threshold `hue=0` red → `hue=215` blue (both `colorForRatio` branches + `.swatch` legend gradient), verified ΔRGB 63–122 under simulation — a real improvement. Owner rejected on sight: the red/green scale is an intentional reference to finviz.com's market-map convention, not an accidental choice — brand identity outweighs this specific gap. Reverted to red/green (`hue=0`/`hue=120`/`hue=130`), including the `.swatch` gradient and legend caption text. **Documented exception**: every cell already renders its numeric ratio as on-cell text (not tooltip-only, see line ~712/756/839) in addition to color, so this was never a hard WCAG 1.4.1 fail (meaning isn't color-only) — colorblind users read the number. `.bubble-swatch` CSS class is unrelated dead code, still not a live issue |
| 13 | `index.html` active-tab color-only (`.tab.active{background:var(--primary)}`) | WCAG 1.4.1, sighted low-vision/monochrome-display users | Added `.tab.active{text-decoration:underline}` in `common.css` — additive, doesn't touch any existing color |
| 14 | 10 chart `aria-label`s are static, not dynamic per company/values | — | Still open — real content-authoring task (live-region or per-render text summary), different category from a color fix, not attempted in this pass |

### 2c. Corrections to the pre-existing `claude-agent-designer.md` §5.3 note

- The `#ff9f40` medium-confidence-badge gap (contrast ≈3.25:1) is **stale** — that literal no longer appears anywhere in the 4 HTML files. Removed from §5.3.
- `--pos`/`--neg`/`--warn` tokens are defined in `:root` but **not yet referenced** as `color:` anywhere in the 4 pages (per the doc's own "adopt progressively" note) — their contrast values (`--warn` 2.15:1, `--pos` 3.30:1 on white) matter for whenever they DO get adopted as text color, not today. Noted here so the eventual adoption doesn't reintroduce these numbers blind.

### 2d. Already-good pattern (no finding, noted for the baseline going forward)

IFRS17.html's waterfall bars (`#22c55e` positive / `#ef4444` negative) are a green/red pair that would normally be a colorblind concern, but every value is *also* rendered with the site's mandatory △ (samo) sign convention — the symbol carries the sign independent of color, and bar position (above/below the running total) is a third redundant cue. This is the model to follow for any new red/green encoding: **never color alone.**

## 3. Verification

- Claude Browser preview, all 4 pages, desktop (1280px) + mobile (375px): 0 console errors.
- `index.html` treemap: dispatched `KeyboardEvent('keydown',{key:'Enter'})` on a cell → navigated to `K-ICS.html?company=...&period=quarter`, same URL a click produces.
- `index.html` mobile list rows: same `tabindex="0"`/`role="link"`/`aria-label` confirmed present at 375px viewport.
- `공시보고서.html`: `document.styleSheets` confirms `common.css` loaded and its `:focus-visible` rule is present.
- `aria-current="page"` confirmed present on the active-tab `<a>` in all 3 pages that have one (K-ICS.html, IFRS17.html, 공시보고서.html); index.html has no self-referencing tab, so no change needed there.

## 4. Local skill

Per the order's delegation ("구현 형태는 위임 — 외부 스킬 설치 vs `skill-creator`로 로컬 스킬. 로컬 권장"): went **local**. `ui-ux-pro-max` isn't installed in this environment and installing an external skill needs its own approval step; more importantly this repo's a11y surface is small and specific (4 static-ish dashboards, a handful of recurring patterns — custom toggles, canvas charts, categorical color palettes) so a generic external auditor would spend most of its budget re-discovering context this project already has written down (design tokens, the owner-gated-value rule, the △ convention). A thin local skill that already knows those constraints is more useful here than a general-purpose one.

Added `.claude/skills/a11y-audit/SKILL.md` — encodes this baseline (§1), the contrast-check script (`scripts/a11y_contrast_check.py`), the colorblind-simulation approach, and the "rendered value → owner-gated, don't auto-fix" rule, so a future designer session can re-run the same methodology instead of starting from zero.

## 5. 2026-10-19 감사 — `compare.html` · `privacy.html` (6페이지로 확대)

범위: 위 4페이지 감사(2026-07-21)에 없던 `compare.html`(사별 비교)과 `privacy.html`(개인정보처리방침·이용안내). 이번에는 **아무것도 고치지 않았다** — 위반은 designer 티켓 `inbox/designer/20261019T1400Z__orchestrator__MULTI_ALL__a11y_compare_privacy.md` 로 보냈다. 색·토큰 값을 바꾸는 항목은 §2b 규칙대로 owner 승인 대상이다.

### 5a. 방법과 한계

- **도구·조건**: Playwright(Chromium headless) + 저장소 루트 로컬 정적 서버(빈 포트). 주소는 전부 `?iq_internal=1`, GA 요청은 route 로 차단해 전송 0. 3분기 안내 팝업은 표시 시작일(2026-10-31) 전이라 시드 없이도 두 페이지 모두 안 뜬다(확인함). 측정 맥락에는 그래도 `iq_notice_seen` 을 심어 두었다.
- **시나리오**: compare = 생보 4사(삼성생명·한화생명·교보생명·신한라이프) / 손보 4사(삼성화재·DB손보·현대해상·KB손보) / 회사 미선택, privacy = 1개. 각각 1280·375 폭 x 라이트·다크(총 18회 실행, reduced-motion 3회 포함). `data/compare/panel_compare.json` 은 다른 세션이 손해율 보기를 편집 중이라 2026-10-19 시점 스냅샷이다.
- **측정**: 텍스트 대비 = 보이는 텍스트 노드(compare 실행당 169~217개, privacy 102개)의 computed color 를 불투명도·조상 배경까지 합성해 WCAG 상대휘도로 계산. 차트 색 = Chart.js 데이터셋·SVG stroke·막대 CSS 값을 `scripts/a11y_contrast_check.py` 로 대비·색각(protan/deutan) 계산. 포커스 = Tab 으로 끝까지 돌며 정지점마다 outline·포커스 전후 픽셀 차이·`elementFromPoint` 가려짐 확인(전환이 끝난 뒤 값으로 재측정). 이름 = aria-label·labelledby·label·내용. 키보드 조작은 실제 키 입력으로 시험.
- **한계**: 실제 스크린리더는 쓰지 않았다(Playwright `aria_snapshot` 으로 이름·역할만 확인). hover 상태의 색과 Chart.js 캔버스 글자 색은 설정값으로만 확인했다. `index`·`K-ICS`·`IFRS17`·`공시보고서` 는 이번에 재측정하지 않았다 — 2026-09-20 에 팔레트가 바뀌었으므로(`common.css` 머리말) §2b 표의 토큰 값(`#6a737a` 등)은 교체 전 값이다. 측정 하니스는 저장소에 넣지 않았다(세션 임시 폴더). 고친 뒤 재측정용 검사 스크립트는 티켓에 요청했다.

### 5b. 통과로 확인한 것 (측정값)

| 항목 | 결과 |
|---|---|
| 텍스트 대비(1.4.3) | 18회 실행 전부 최소 라이트 **5.28:1** · 다크 **6.10:1**(탭 `K-ICS` 글자 `--muted` 위 `--card`). 예외 1건은 C4. 비활성 입력창의 placeholder(4.22:1)는 비활성 컨트롤이라 면제 |
| 포커스 링(2.4.7) | Tab 정지점 compare 4사 63·손보 62·미선택 8, privacy 11~12개가 문서 끝까지 이어지고 키보드 함정 없음(375 폭은 25개 뒤 처음으로 순환). 링 2px solid, 배경 대비 라이트 **6.09:1**(칩 안 5.58) · 다크 **7.26:1**(칩 안 6.49). 활성 `.seg-btn` 안쪽 흰 링 6.09:1(다크 7.62), 모바일 섹션 FAB 17.72:1(다크 14.76). 포커스 전후 픽셀 차이 없는 정지점 0, 다른 요소에 가려진 정지점 0 |
| 이름·라벨(3.3.2·4.1.2) | 이름 없는 컨트롤 0, 중복 id 0, 끊긴 aria 참조 0(18회 전부). 검색창은 sr-only label + combobox/listbox 패턴, 칩 제거 버튼은 「OO 제거」, 활성 탭은 `aria-current="page"` |
| 키보드 조작 | 검색창 ↓ 열림·`aria-activedescendant`·Enter 선택·Esc/Tab 닫힘. 공유 메뉴 Enter → 첫 항목 포커스, ↓ ↑ Home End, Esc 시 버튼으로 복귀, Tab·바깥 클릭 닫힘. 구분 토글은 Space/Enter 뒤에도 같은 버튼이 포커스를 유지하고 스크롤 이동 0(경과조치 토글도 포커스 유지). 지표 가이드 Alt+↓ 순서 이동(「지급여력비율 표시 순서 2번째로 이동」 안내), 링크 Enter → 카드에 포커스. 모바일 FAB Enter → 시트 안으로 포커스, Esc → FAB 복귀 |
| `?` 팝오버(키보드·위치) | 포커스로 열리고 Esc 로 닫힌다(1.4.13 해제 가능). 375 폭에서 실제 탭한 5곳과 1280 폭 12곳 전부 화면 안(375 폭 `[8,348]`). 마우스 경로는 C1 |
| 반응형·리플로 | 1280·375·320 에서 가로 넘침 0(`scrollWidth` = `innerWidth`) |
| 다크·콘솔 | 다크 7회 실행이 위 표와 같은 기준 통과(placeholder 제외). 콘솔 오류 0(내가 막은 GA 요청 제외) |
| reduced motion(CSS) | 1ms 초과 전환 요소 44개 → 0개. Chart.js 는 C11 |
| privacy | 텍스트 5.28~6.10:1, 표 `th scope="col"`, 본문 링크 밑줄 + `--primary-hover`(5.58:1), 가로 넘침 0 |

### 5c. 지적 사항

심각도: **중간** = WCAG 2.1 AA 기준 위반 가능성이 큼, **낮음** = 보조기기 사용성·개선 권장, **참고** = 2.1 AA 요건 밖(2.2 또는 AAA).
위치 앞의 「공통」은 `common.css`·`theme.js` 라 6페이지 전부에 해당한다는 뜻이다. 색·토큰 값이 바뀌는 항목은 owner 승인 대상(§2b).

| # | 심각도 | 위치 | 측정값 | 제안 |
|---|---|---|---|---|
| C1 (처리됨, §5e) | 중간 (1.4.13 가리킨 뒤 이동 가능) | 공통 `common.css` `.iq-help-pop` | 버튼 하단 y=314, 팝오버 상단 y=320, 사이 6px 틈에서 `:hover` 가 풀려 `pointer-events:none`. 1px 단위로 내려가면 y=315 불투명도 0.84 → y=323 0, 팝오버 안으로 못 들어감 | 팝오버에 `::before{content:"";position:absolute;left:0;right:0;top:-8px;height:8px}` 다리를 둔다(팝오버의 자식이라 hover 유지). 값이 안 바뀌는 추가 규칙 |
| C2 (처리됨, §5e) | 중간 (2.4.3 포커스 순서) | `compare.html` 칩 제거·회사 추가 | 칩 제거 버튼에서 Enter → `activeElement` = `body`. 4번째 회사를 키보드로 추가하면 입력창이 비활성되며 포커스가 `body` 로 | 제거 뒤 다음(없으면 이전) 칩의 제거 버튼, 없으면 검색창으로 `focus()`. 4곳이 차면 첫 칩 제거 버튼으로 |
| C3 (처리됨, §5e) | 중간 (1.4.11 UI 경계) | 공통 `--border` 를 쓰는 입력창·`?` 버튼·구분 토글 | 검색창 테두리 `#e4e4e2` on `#fff` **1.27:1**(다크 `#313431` on `#151615` 1.44:1). 입력창은 글자 라벨이 없어 테두리가 경계의 유일한 단서 | 입력창·체크박스용 새 토큰 `--control-border`(예: 라이트 `#85888d` 3.56:1, 다크 `#727772` 3.97:1)를 만들어 폼 컨트롤에만 쓴다. `--border` 값은 안 건드림. owner 승인 |
| C4 (처리됨, §5e) | 중간 (1.4.3) | 공통 입력창 `::placeholder` | 다크에서 UA 기본 `#757575` on `#151615` **3.94:1**(라이트 4.61:1 통과). compare 검색창은 label 이 sr-only 라 placeholder 가 시각 라벨 | `input::placeholder{color:var(--muted)}`(라이트 5.76, 다크 6.83). 라이트 색이 약간 바뀌므로 owner 승인 |
| C5 (owner 거절, §5e) | 중간 (1.4.11·1.4.1) | `compare.html` 유지율 묶음 막대 `PAL_BAR` (넓은 화면 Chart.js) | 라이트 흰 배경 대비 `#8ccfc6` 1.77 · `#f6b49f` 1.76 · `#a8c1f0` 1.82 · `#e6d27e` **1.51:1**(다크는 9.98~12.00 통과). 색각 쌍 `#f6b49f`/`#e6d27e` ΔRGB 12·9, `#8ccfc6`/`#a8c1f0` 31·30. 완화 요소: 막대 위 수치 라벨, 묶음 안 고정 순서, 범례 | 막대에 어두운 윤곽(예: `#4a9d92`·`#d9764f`·`#6f94d6`·`#a38d1f` 각 3.05~3.29:1, `borderWidth` 1.5)을 두거나 팔레트를 어둡게. 팔레트 변경이라 owner 승인 |
| C6 (처리됨, §5e) | 중간 (1.4.1) | `compare.html` 좁은 화면(≤640px) 손해율 SVG 꺾은선·표 견본 | 선이 모두 실선이고 마커·직접 라벨이 없어 색으로만 구분. 손보 4사에서 현대해상 `#ea690c` / KB손보 `#b88700` ΔRGB **40·49**(<60)(다크 `#F47920`/`#FFBC00` 48·47). 넓은 화면은 마커 모양(원·삼각·사각·마름모)이 있어 통과 | SVG 선에 넓은 화면 `PT` 와 같은 마커 모양을 달고 표 견본에도 같은 모양을 쓴다 |
| C7 (owner 거절, §5e) | 낮음 (1.4.11) | `compare.html` 손해율 선 폴백 팔레트 `PAL_LINE` (`lcShown`) | 코드 주석은 선·배경 3:1 이라 하지만 `visibleOn` 은 키컬러에만 적용. 라이트 `#4fb0a5` 2.60 · `#ee8f72` 2.38 · `#7b9fe6` 2.64 · `#cdb04a` **2.12:1**. 생보 4사 선택 시 신한라이프가 `#7b9fe6` | `lcShown` 이 폴백 색에도 `visibleOn` 을 적용(예: `#3a9a8f` 3.39 · `#e0693f` 3.35 · `#5f87dd` 3.50 · `#a68a1c` 3.35). 표시 색이 바뀌므로 owner 승인 |
| C8 | 낮음 (1.3.1·2.4.6) | `compare.html` 카드 `h3` | `h3` 안에 `?` 버튼과 `role=tooltip` 설명이 들어가 제목의 접근 이름에 설명이 붙음. 이름 길이 56~585자(손해율 카드 585자) | `.iq-help` 를 `h3` 밖 형제로 옮기거나 `h3` 에 짧은 `aria-label` |
| C9 | 낮음 (2.4.6·4.1.2) | 공통 `theme.js` 섹션 공유 버튼 | compare 10개가 전부 `aria-label` = 「이 섹션 스크린샷 공유」(섹션 이름은 `title` 뿐이고 `aria-label` 이 우선) | `aria-label` = 「<섹션 이름> 스크린샷 공유」 |
| C10 | 낮음 (2.4.1 블록 건너뛰기) | `compare.html`·`privacy.html` | 두 페이지 모두 `<main>` 과 건너뛰기 링크 없음. compare 데스크톱에서 첫 카드 컨트롤까지 Tab **38번**(칩 4·가이드 링크 10·빼기 버튼 10 포함), privacy 본문 첫 링크까지 8번 | 본문 컨테이너를 `<main>` 으로, 머리말 앞에 「본문으로 건너뛰기」 링크, 가이드 빼기 버튼은 `tabindex="-1"`(Delete 키는 유지) 검토 |
| C11 | 낮음 (감소 모션) | `compare.html` Chart.js · 공통 `theme.js` | reduced-motion 에서도 `Chart.defaults.animation.duration` **1000**(차트 2개 모두). `theme.js` `scrollBy({behavior:'smooth'})`(터치 팝오버 보정)는 reduce 판정이 없음(다른 두 곳은 판정함) | `IQTheme.applyChartJs` 에서 reduce 면 `animation=false`, `scrollBy` 도 reduce 면 `auto` |
| C12 | 낮음 (4.1.3 상태 메시지) | `compare.html` 경과조치 토글·중앙값 체크박스 | 두 조작 뒤 `#live` 가 직전 값(「구분 Non-Par」) 그대로 — 카드가 다시 그려져도 안내 없음(칩·지표 이동·구분은 `say()` 함) | 두 `change`/클릭 핸들러에서 `say()` 호출 |
| C13 | 낮음 (4.1.2) | 공통 `theme.js` 테마 토글 | `aria-pressed` 와 상태별로 바뀌는 `aria-label` 을 같이 씀: 「다크 모드로 전환」(false) → 「라이트 모드로 전환」(true). 「라이트 모드로 전환, 눌림」 으로 읽혀 모호 | 레이블을 고정하고 `aria-pressed` 만 바꾸거나, 레이블만 바꾸고 `aria-pressed` 제거 |
| C14 | 낮음 (1.1.1) | `compare.html` 넓은 화면 손해율 꺾은선 | `canvas` `aria-label` 이 선마다 시작값→끝값만 담음(예: 삼성생명 88.4%에서 97.1%). 좁은 화면은 표가 있고 유지율 막대는 모든 값을 담아 통과. Chart.js 범례 클릭 토글·툴팁은 포인터 전용 | 좁은 화면의 현재가치 표를 넓은 화면에도 `<details>` 로 제공 |
| C15 | 낮음 (4.1.2) | `privacy.html` `.policy-table-wrap` | 375 폭에서 가로 스크롤 영역이 Tab 정지점이지만 역할·이름이 없음 | `role="region"` · `aria-label="처리 위탁 표"` · `tabindex="0"` |
| C16 | 참고 (2.5.8 은 WCAG 2.2, 2.5.5 는 AAA) | 공통 `?` 버튼·체크박스·레일 빼기·브랜드 링크 | 24px 미만: `?` 22x22(compare 12개), 체크박스 18x18, 레일 빼기 22x22, 375 폭 브랜드 링크 높이 19px. 44px 미만: 탭 33, 테마·공유 30, 칩 제거 28, 구분 버튼 28 | 2.2 AA 를 목표로 삼을 때 24px 이상으로 |
| C17 | 참고 (1.3.1) | `compare.html`·`privacy.html` 제목 | compare 는 `h1` 다음이 바로 `h3`(`h2` 없음), privacy 는 `h1` 이 둘(개인정보처리방침·이용안내) | 카드 제목을 `h2` 로, 두 번째 문서는 `h1` 유지 가능 |
| C18 (owner 거절, §5e) | 참고 (1.4.11) | `compare.html` 막대 카드 | 처음 고른 회사 외 막대 = `--muted` 불투명도 .65 → 라이트 `#9a9c9f` on `#fff` **2.75:1**(다크 3.61 통과). 막대마다 수치 글자가 함께 있어 정보는 중복됨 | 불투명도 .65 를 .8 쯤으로(색 변화라 owner 승인) |

### 5d. 후속

위반 C1~C18 은 designer 티켓 한 건(`inbox/designer/20261019T1400Z__orchestrator__MULTI_ALL__a11y_compare_privacy.md`)에 묶었다. 색·토큰 항목(C3·C4·C5·C7·C18)은 owner 승인 뒤에만 고친다. 색을 바꾸지 않는 항목(C1·C2·C6·C8~C17)은 §2a 처럼 바로 고칠 수 있다.

### 5e. 처리 현황 (2026-10-19)

owner 구두 결정(「접근성 추천대로」): C1 · C2 · C3 · C4 · C6 만 한다. C3 · C4 색 변경은 승인(글자 입력창 테두리와 placeholder 만, 차트 색 그대로). C5 · C7 · C18 은 하지 않는다(수치가 함께 표시돼 정보가 겹침). C8 ~ C17 은 범위 밖이라 열려 있다. 재측정·회귀 검사는 `scripts/check_a11y_compare_privacy.py`(1280/375 x 라이트/다크 x compare 3 시나리오, 단언 3357개, 수집기 요청 0).

| # | 상태 | 고친 곳 | 고친 뒤 측정 |
|---|---|---|---|
| C1 | 처리됨 | `common.css` · `theme.js`. ① `.iq-help-pop::before` 다리: 버튼과 팝오버 사이 6px 틈을 덮는다(위로 열 때 `--up` 은 아래쪽). ② 마우스 유예: `.iq-help` 를 떠난 뒤 400ms 동안 `theme.js`(`pointerleave`/`pointerenter`, 터치 제외)가 `is-grace` 를 붙이고 `common.css` 가 그동안 팝오버를 유지한다(Esc 로 닫은 상태가 우선). 모양·크기를 더하지 않아 이웃 컨트롤을 가리지 않고 문서를 넓히지 않는다. 처음 시도한 버튼 옆 삼각형 호버 영역은 화면 오른쪽 끝의 `?` 에서 호버 중 문서를 가로로 넓혀(375 폭 `index` +89px · `K-ICS` +92px, 독립 검증자가 발견) 버리고 이 방식으로 바꿨다 | 마우스 경로(수직 우선 · 직선 대각선 · 아래로 휜 곡선, 버튼 중앙에서 팝오버 중앙까지)에서 `opacity` 1 · `pointer-events:auto` 유지(버튼 39개). 옆으로 먼저 멀리 갔다 내려오는 곡선은 400ms 를 넘으면 풀려 참고만 한다. 다리·유예를 끈 음성 대조에서는 풀림. 키보드 열림·Esc 닫힘 그대로, 375 폭 좌우 [7.6,363]. 호버 중 가로 넘침: `?` 버튼 115개 전수에서 `scrollWidth` − 화면 폭 = 0(1280 · 375 마우스). 탭 뒤에 남는 `:hover` 는 Playwright 터치 에뮬레이션이 만들지 못해 실기기로는 못 쟀다 |
| C2 | 처리됨 | `compare.html` 칩 제거 · 회사 추가 핸들러 | 제거 4단계·4곳 추가 모두 `activeElement` 가 보이는 컨트롤(다음 칩 > 이전 칩 > 검색창, 4곳째는 첫 칩 제거 버튼), `#live` 문구 일치. 마우스로 마지막 칩을 뺄 때는 검색창을 열지 않음 |
| C3 | 처리됨 | `common.css` 새 토큰 `--control-border`(라이트 `#85888d` · 다크 `#727772`) — `input#addco`, `.iq-input`, `.iq-textarea` 에만. `--border` 값 그대로. 선택 상자·네이티브 체크박스는 안 바꿈(체크박스 실측 라이트 4.54 · 다크 4.92:1 로 이미 통과) | 검색창·오류 제보 입력창 테두리 라이트 3.56 · 다크 3.97:1(옛 1.27 · 1.44) |
| C4 | 처리됨 | `common.css` `input::placeholder, textarea::placeholder{color:var(--muted);opacity:1}` | placeholder 라이트 5.76 · 다크 6.83:1(옛 다크 3.94) |
| C6 | 처리됨 | `compare.html` `lossMobile`(표식 · 견본) | 선마다 서로 다른 모양(원 · 삼각 · 사각 · 마름모, 선택 순서) = 표 견본 모양 = 넓은 화면 `pointStyle`, 색 불변. 흐린 점선 구간 표식은 속 빈 표식으로 구간마다 1개 이상 |
| C5 · C7 · C18 | owner 거절 | 변경 없음 | `PAL_BAR` · `PAL_LINE` 원문 일치를 검사 스크립트가 단언 |
| C8 | 처리됨 | `compare.html` 카드 제목 `h2 aria-label="제목 단위"`(`?` 버튼·설명은 제목 안에 그대로, `aria-describedby` 유지) | 접근성 트리 제목 이름 최대 16자(옛 판 제목 내용 최대 840자, 손해율 카드). 모양 불변(16px · 600 · 여백 0 · 오른쪽 44px) |
| C9 | 처리됨 | `theme.js` `mountSectionShare` 「섹션이름 스크린샷 공유」(같은 이름이 또 나오면 「2번째」) | 6페이지 x 1280/375 x 라이트/다크 모두 한 페이지 안 이름 중복 0, 섹션 이름 포함(한 페이지 최대 10개) |
| C10 | 처리됨 | `compare.html`·`privacy.html` `<main tabindex=-1>` + `common.css` `.iq-skip`(포커스 때만 보임) + `theme.js` 클릭 핸들러(해시를 안 바꿔 popstate 재렌더 없음). compare 는 링크 2개(본문 · 비교 카드), 레일 빼기 버튼 `tabindex=-1`(Delete 키·마우스 그대로) | 첫 Tab 에 링크가 보이고 Enter 로 main 포커스. compare 건너뛰기로 첫 카드 컨트롤까지 Tab 3번(+Enter), 순서대로 Tab 은 38 -> 30(링크 2개 포함). privacy 건너뛰기 Tab 2번, 순서대로 8 -> 9 |
| C11 | 처리됨 | `theme.js` `applyChartJs`(reduce 면 `Chart.defaults.animation=false`) · `scrollBy` behavior | reduce 에서 compare 차트 2개 `options.animation` false(보통 환경 0개), 375x320 터치 `scrollBy` behavior reduce `auto` / 보통 `smooth` |
| C12 | 처리됨 | `compare.html` 경과조치·중앙값 핸들러가 `say()` | `#live` 「경과조치 적용 전/후」 · 「같은 유형 업계 중앙값 표시/숨김」 일치 |
| C13 | 처리됨 | `theme.js` `decorate` 바뀌는 레이블만, `aria-pressed` 제거 | 6페이지 x 2 뷰포트 x 2 색 구성표: 클릭 전후 모두 `aria-pressed` 없음, 레이블 「다크 모드로 전환」 <-> 「라이트 모드로 전환」 |
| C14 | 처리됨 | `compare.html` `lossChart` 가 `.sr-only` 현재가치 표(`.lcpv`)를 카드에 추가 | 넓은 화면 생보·손보 4사에서 표 1x1px(레이아웃 불변), 접근성 트리에 `table`/`columnheader`, 값이 범례 「현재가치 N%」 와 같음(최대 5행). 좁은 화면은 기존 표만 |
| C15 | 처리됨 | `privacy.html` `.policy-table-wrap` `role=region` + `aria-label`(처리 위탁 표 · 데이터 출처 표) + 가로로 넘칠 때만 `tabindex=0`(작은 스크립트) | 375 폭 처리 위탁 표만 넘쳐 `tabindex=0`(데이터 출처 표는 안 넘쳐 Tab 정지점 아님, 1280 은 둘 다 없음). 키보드 포커스 링 라이트 6.09 · 다크 7.26:1, 마우스 클릭엔 링 없음 |
| C16 | 열림 | owner 가 WCAG 2.1 / 2.2 목표를 먼저 정해야 함 | — |
| C17 | 처리됨 | `compare.html` 카드 제목 `h3` -> `h2`(css `.card h2`) | h1 1 -> h2 N 순서(건너뜀 0), 계산된 모양 불변. privacy 둘째 `h1` 은 유지 |

덤: 375 폭 손해율 카드 `?` 팝오버가 키보드 포커스·탭에서 화면 왼쪽 밖(`[-291,49]`)에 남던 기존 버그를 고쳤다(`theme.js` 의 화면 안 보정이 `compare.html` 의 방향 전환보다 먼저 돌아 낡은 위치가 남음 → `IQTheme.clampHelpPops` 를 노출해 전환 뒤 다시 호출). 옛 판에서도 같은 값으로 재현됐다.
