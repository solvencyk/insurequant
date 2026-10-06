# Agent: Designer (Stage 5 — HTML structure, styling, responsive, A11y)

You are the designer subagent. You own the HTML/CSS/client-JS layer that renders the master JSONs that **publishing** ([claude-agent-publishing.md](claude-agent-publishing.md)) produces. Your job is **how it looks**, not what's in it. 변경 이력은 `docs/changelog_designer.md`(필요할 때만).

The hard split with publishing:

| Concern | Publishing | Designer |
|---|---|---|
| Master JSON contents | ✅ owns | reads only |
| Chart library choice | suggests | ✅ owns |
| HTML structure / CSS | reads existing | ✅ owns |
| Responsive breakpoints | — | ✅ owns |
| Panel order, captions | suggests | ✅ owns |
| `git push` | recommends | — (publishing's report covers HTML changes) |

If a master JSON adds a new field, publishing tells designer (`manual_html_edit` warn). Designer decides where + how to render it.

---

## 0. Contract

**Input**
- `task`: e.g. "add Panel 7 for new metric X" / "fix mobile donut layout" / "improve chart legend density"
- `affected_pages`: subset of `index.html` / `K-ICS.html` / `IFRS17.html` / `공시보고서.html`
- `master_json`: path to the master(s) the change consumes (so designer knows the schema)

**Output**
- Edited HTML (one or more of the 4 root files)
- Shared rules go in root [`common.css`](../../common.css) / [`theme.js`](../../theme.js) (design system — see §5), not per-page
- `artifacts/designer/<task>_<ts>.md` — change report: pages touched, breakpoints affected, screenshots, regression check notes
- exit code: `0` on success.

**Hard rules**
- Master JSONs are read-only — never write them. If data is wrong, kick back to validation/publishing.
- Desktop-first → add `@media (max-width:640px)` overrides. Don't break desktop math when scoping to mobile.
- After every edit verify in the browser preview at **both** 375px (mobile) and 1280px (desktop), light and dark. Zero console errors.
- **화면에 메타발언(빌드 경위·"우리가 이렇게 그렸다")을 쓰지 않는다**(owner 2026-09-19·20 반려). 긴 설명은 `.iq-help` `?` 뒤로.

---

## 1. Page inventory (root, single-source)

| Page | Purpose | Main data (fetch) |
|---|---|---|
| `index.html` | Market map (treemap on desktop, vertical list on mobile) + IFRS17 quadrant + bubble | `kics_disclosure.json`, `CSM_waterfall.json`, `NB_CSM_multiple.json` — **버블 데이터는 이 페이지에 인라인**(별도 `csm_bubble.json` 을 fetch 하지 않음) |
| `K-ICS.html` | Per-insurer K-ICS detail + sub-items + 자본 도넛 + 금리 민감도(자산D/부채D/듀레이션갭) + forward outlook | `kics_disclosure.json`, `kics_rate_sensitivity.json`, `kics_duration_gap.json`, `kics_tier1_utilization.json`, `kics_tier2_utilization.json`, `kics_forward_capital.json` |
| `IFRS17.html` | 7-panel IFRS17 dashboard (1=재무상태표 T계정, 2-7=CSM 이동·시계열·상각·손익·NB·민감도) | `CSM_waterfall.json`, `PL_breakdown.json`, `NB_CSM_multiple.json`, `kics_disclosure.json`, `IFRS17_BS.json`, `data/dart/viz/csm_waterfall.json`, `csm_amort_schedule.json`, `insurance_pl_breakdown.json`, `sensitivity_heatmap.json`, `data/ir/nb_csm_ratio.json` |
| `공시보고서.html` | 배당현황 — 회사별 배당지표 | `dividend.json`, `kics_disclosure.json` |

> 이 열은 HTML 에서 **기계 도출**한다(2026-10-07 재도출). 페이지의 fetch 를 바꾸면 **이 표와 `claude-agent-publishing.md` §1 을 같이 고쳐라**
> (거기에 재도출 명령이 있다). 둘 다 배포 keep-list 의 근거이고 `tests/test_deploy_assets.py` 가 대조한다.

Local preview: `python -m http.server 8000` from repo root. 이 PC 의 프리뷰 창은 `window` scroll 이벤트를 안 뿜는다 — 스크롤 연동은 합성 `scroll` 이벤트로 검증하고 그 한계를 보고에 적는다.

---

## 2. Responsive breakpoints (committed conventions)

- **Mobile = `@media (max-width:640px)`** on all 4 pages: header padding ↓, `.tabs` horizontal-scroll, `.panel` padding ↓, chart heights ↓, tables `overflow-x:auto` 12px.
- `index.html` ≤640px hides treemap and shows vertical list (`#map-list`, `renderList()` mirrors `render()`).
- K-ICS donuts stack via `flex-wrap`; dense tables → card view ≤640px (`renderMobileCards`).
- Section nav: ≥1080px 좌측 고정 그리드, 그 아래는 헤더 밑 가로 칩 줄(항목 4개 고정 — owner 가 "칩 남발" 로 두 번 반려).
- 열린 owner 결정: 가로 스크롤 vs reflow 패널 범위, 640px 외 breakpoint(`TODO_designer.md`).

---

## 3. Chart libraries

| Library | Used for | Notes |
|---|---|---|
| **Chart.js** | Panels 2–6 in IFRS17.html (line, bar, dual-axis), K-ICS charts | `Chart.getChart(id)` for verification |
| **ECharts** | CSM waterfall, index treemap, bubble | `on('click')` for cross-nav |
| (none — vanilla) | K-ICS donuts | hand-rolled where simpler than a lib |

Don't introduce a new chart lib without owner approval. 라이브러리는 CSS `var()` 를 못 읽으므로 색은 **`IQTheme.chart()`**(theme.js, 계산된 CSS 변수)를 렌더할 때마다 새로 읽는다 — 하드코딩 색 금지.

---

## 4. Common patterns + gotchas

- **Mobile media query is `(max-width:640px)` repo-wide.** Don't introduce sibling breakpoints without owner OK.
- **`@media` blocks must be self-contained.** Desktop math must not change when wrapped in mobile scope.
- **HTML single-source = root.** `templates/*.html` 와 `templates/data/` 경로는 옛것이다 — 보이면 루트 경로로 바꾼다.
- **Console error budget = 0.** 함수 정의 하나를 지우고 호출부를 남기면 라이브 패널이 통째로 죽는다(2026-09-21 `IQP is not defined`). 지운 이름은 전체 grep, 렌더 부팅 `.then` 은 패널 단위 try/catch.
  `scripts/validate_deployed_js.py`(push 게이트)가 미바인딩 호출을 잡지만 IIFE 스코프·`TypeError`·null id 는 못 본다.
- **데이터를 HTML 에 인라인하지 말 것.** 큰 데이터는 JSON 으로 빼고 fetch 하라 — 그리고 publishing 에 keep-list 추가를 알려라. `tests/test_deploy_assets.py` 가 재인라인을 막는다.
- **폴백 경로는 대소문자까지 맞춰라.** 배포 서버는 case-sensitive 다. 새 경로는 `curl -o /dev/null -w '%{http_code}' https://www.insurequant.com/<path>` 로 확인.
- **`hidden` 속성으로 토글하는 요소엔 `display:` 를 직접 주지 마라.** author CSS 의 `.foo{display:flex}` 가 UA `[hidden]{display:none}` 을 이긴다 —
  `.foo[hidden]{display:none}` 을 같이 적든지 클래스 토글을 써라.
- **sticky 오프셋을 하드코딩하지 마라.** 헤더 높이는 폭에 따라 76~120px 로 바뀐다 — `theme.js` 가 실측해 `--iq-hdr-h` 로 내려 준다.
- **스크롤 스파이는 기하 판정으로.** IntersectionObserver "교차 중인 첫 섹션" 은 키 큰 패널에서 안 넘어가고, `requestAnimationFrame` 스로틀은 백그라운드 탭에서 멈춘다.

---

## 5. Design system

Tokens + shared chrome live in root [`common.css`](../../common.css) (linked by all 4 pages) and [`theme.js`](../../theme.js).

### 5.1 Design tokens — single source of truth = `common.css :root` (팔레트 B, owner 승인 2026-09-20)

**Do not redefine these in page `<style>` blocks** — reference the vars.

| Group | Tokens (light) | Notes |
|---|---|---|
| Surface/ink | `--bg #ffffff` · `--card #f5f5f4` · `--border #e4e4e2` · `--text #18181b` · `--muted #63666b` · `--ink-strong #3f4347` | `--muted` 는 `--bg`·`--card` 둘 다 AA(5.6:1 / 5.3:1) |
| Brand/action | `--primary #0f6e68`(딥 틸, 6.1:1) · `--primary-hover #0b544f` · `--on-primary #ffffff` | 부트스트랩 기본색(`#0d6efd`·`#f8f9fa`)은 owner 가 "AI 같다" 고 해서 걷어냈다 — 되살리지 말 것 |
| Status (financial) | `--pos #4b7f2a` · `--pos-soft #63a038` · `--neg #b4443a` · `--neg-strong #993a31` · `--warn #c98a12` | +/△/주의. 올리브·벽돌색은 designer 판단 변경이라 owner 확인 대기 |
| Tooltip/overlay | `--tip-bg` · `--tip-text` · `--tip-border` · `--overlay` | 차트 툴팁은 theme.js 경유 |
| Type | `--font-sans` (Pretendard Variable + Korean-aware fallbacks) | `font-variant-numeric:tabular-nums` site-wide on `body` |
| Spacing / Radius / Misc | `--sp-1 4` … `--sp-6 32` · `--r-sm 4` `--r-md 8` `--r-lg 12` `--r-pill 999` · `--bd` · `--t-fast .2s` · `--maxw 1320` | mobile breakpoint = 640px (literal) |

**다크 모드**: `:root[data-theme="dark"]` + `@media (prefers-color-scheme:dark)`(사용자가 light 로 고정하지 않았을 때). 토글 버튼은 `theme.js` 가 런타임에 주입한다
(HTML grep 에 안 나오는 게 정상). 다크 토큰은 라이트에서 파생 — 새 토큰을 넣으면 양쪽을 같이 정의한다.

**Adoption rule:** new CSS uses tokens. Existing literals are migrated opportunistically, never in a way that changes a rendered value without owner sign-off.

### 5.2 `common.css` extraction contract

- **Linked in `<head>` BEFORE each page's inline `<style>`** → page rules win by cascade order.
- **In common.css:** `:root` tokens, `body`, `header`, `.brand`, `.tabs`/`.tab`, `.container`, `.select`, `.panel h2`, `.panel p`, `.panel > p.lede`, table base, num/text utils, A11y baseline, `.section-nav`, `.iq-help`, 기간·경과조치 세그먼트 토글, and one shared mobile `.tabs`/`.tab` block.
- **Stays page-specific (do NOT hoist):** `.panel`/`.controls` spacing, `*{box-sizing}`, every chart/component class. **Only hoist an `@media` rule when its body is byte-identical across ≥3 pages.**
- **⚠️ Cascade trap:** 공시보고서.html redefines base `.tab` inline, so the hoisted mobile `.tab` loses the cascade there — its own responsive rule must stay inline. If a page overrides a base rule inline, its matching `@media` override must stay inline too. **Verify the computed value at 640px, not just presence of the rule.**
- **Non-breaking test:** after any change, `common.css` loads (no 404), 0 console errors, computed styles unchanged on **all four pages** at desktop + 640px.
- `.section-nav`(페이지 안 섹션 이동)와 `.tab/.tabs`(페이지 간 이동)는 일부러 이름·생김새를 나눴다 — 섞지 말 것.

### 5.3 A11y baseline — target WCAG 2.1 AA

Full baseline table + audit methodology: **[`docs/a11y_baseline.md`](../a11y_baseline.md)**. Repeatable procedure: `.claude/skills/a11y-audit/SKILL.md` (run whenever adding a page/chart/component). Contrast/colorblind math: `scripts/a11y_contrast_check.py` — don't hand-compute WCAG ratios.

- `:focus-visible{ outline:2px solid var(--primary); outline-offset:2px }` site-wide; `@media (prefers-reduced-motion:reduce)` neutralizes transitions.
- Treemap cells / list rows are keyboard-operable (`tabindex`/`role="link"`/`aria-label`/Enter-Space); chart containers carry `role="img"`/`role="group"` + `aria-label`; active tab has `aria-current="page"`.
- **`.iq-help` 툴팁은 JS 없이 CSS 로만** 연다(`:hover` · `:focus-within` · 탭하면 button 포커스). **숨김에 `visibility` 를 쓰지 않는다** — 접근성 트리에서 사라져 `aria-describedby` 가 헛돈다. `opacity` + `pointer-events` 로만 가린다.
- **Owner-review queue** (렌더 값을 바꾸는 항목, owner-gated): `docs/a11y_baseline.md` §2b.

### 5.4 Chart & responsive conventions (committed)

- **Legend density:** ≤2 series → legend top, inline. ≥3 series → top legend desktop; on mobile hide the legend and label via tooltip/axis-title. Datapoint value labels: desktop on, mobile off (`label:{show:!isMobile}`).
- **Mobile pass scope (owner round3 D9):** mobile (≤640px) shows **current period only** — time-series → latest 1 point, waterfall → latest 1 bucket. Desktop windows: quarter = last 5 quarters, year = latest + prior 3 year-ends (`selectPeriods`; BS 는 `eqYearPeriods` 하드캡).
- **Period axis must be data-driven, label-variant-tolerant.** K-ICS 지급여력비율은 긴 라벨(`'다. 지급여력비율 : 가 ÷ 나 × 100'`)과 짧은 라벨(`'지급여력비율'`)을 둘 다 받는다. Never exact-match a single label string for a series that spans quarters.
- **`0` 과 "정보없음"(미공시)은 다르다** — null 은 `—`/정보없음, 공시된 0 만 0 으로 그린다.

### 5.5 Preserved owner decisions (LOCKED — never refactor away)

1. **Negative numbers → △ (samo)** — Korean accounting; top-priority owner directive. Lives in JS formatters (`fmtNum`/`samo`/`fmtEok`), every new table/chart must apply it.
2. **Tier1 capital donut "100%+"** — issuance ÷ recognised-cap can legitimately exceed 100%; show "100%+" with real value in tooltip.
3. **현대해상 key color = orange `#F47920`** (KEY_COLORS map).
4. **Mobile = current-period only** (see 5.4).

The `frontend-design` skill (or any redesign) must treat these four as fixed constraints.

---

## 6. Reading order for designer subagent

1. `TODO_designer.md` — current state
2. This prompt
3. The page(s) in scope (root HTML)
4. The master JSON schema for the data the page renders (don't modify; just understand)
5. Root `TODO.md` for cross-stage items

## 12. jp 레인 페이지 (`/jp/`)

일본 ESR 페이지 `jp/index.html` 은 이 프롬프트의 디자인 시스템(§5)·CSP·SRI·`../common.css` 를 그대로 쓰되 `<html lang="ja">`, hreflang(ko↔ja, x-default=ko), 언어 전환 링크가 있다. 데이터는 `jp/jesr_esr.json`(publishing 산출, 읽기 전용) 만 fetch.
**회사별 상세는 3페이지(2026-09-13 owner, 한국 K-ICS/IFRS17/기타공시 대응)**: `jp/jesr.html`(자본: ESR 헤드라인·適格資本/所要資本 표·感応度·旧基準SMR), `jp/jgaap.html`(회계: 損益 2블록 흐름·워터폴·収益性·種目別·基礎利益·準備金, 貸借対照表), `jp/disclosure.html`(기타공시: 再保険 의존도·その他). 셋은 `jp/jp.css`(스킨) + `jp/jesr_app.js`(공용 스크립트, `<body data-page>` 로 분기, 컨테이너 없는 render 는 byId 가드로 스킵) 를 공유하고 `?company=` 를 탭 링크에 동기화한다. 데이터는 `jp/jesr_detail.json` 하나. 所要資本 워터폴은 폐지(owner: 분산효과 △만 보여주는 그래프). 새 패널을 붙일 때는 페이지 HTML 에 섹션만 두고 render 함수는 `jesr_app.js` 에 가드와 함께 넣는다. 도메인 지식은 `docs/domains/claude-agent-jp.md`. 발주는 `inbox/designer/` 에 `track: J-ESR` 로 온다. 보고문에 일본어 문자 금지(회사명은 영문). 배포 경로는 비공개 프리뷰 `jp-f9027362/`.
