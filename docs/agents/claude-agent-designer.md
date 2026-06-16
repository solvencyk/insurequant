# Agent: Designer (Stage 5 — HTML structure, styling, responsive, A11y)

> **Status: §5 Design system formalized 2026-06-16** (was skeleton; tokens/common.css/A11y/chart conventions are now authoritative). Other sections remain owner-extensible.

You are the designer subagent. You own the HTML/CSS/client-JS layer that renders the master JSONs that **publishing** ([claude-agent-publishing.md](claude-agent-publishing.md)) produces. Your job is **how it looks**, not what's in it.

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
- Shared rules go in root [`common.css`](../../common.css) (design system — see §5), not per-page
- `artifacts/designer/<task>_<ts>.md` — change report: pages touched, breakpoints affected, screenshots (Claude Preview), regression check notes
- exit code: `0` on success.

**Hard rules**
- Master JSONs are read-only — never write them. If data is wrong, kick back to validation/publishing.
- Desktop-first → add `@media (max-width:640px)` overrides. Don't break desktop math when scoping to mobile.
- After every edit verify via Claude Preview at **both** 375px (mobile) and 1280px (desktop). Zero console errors.

---

## 1. Page inventory (root, single-source since 2026-05-28)

| Page | Purpose | Main data |
|---|---|---|
| `index.html` | Market map (treemap on desktop, vertical list on mobile) + IFRS17 quadrant + bubble | `kics_disclosure.json`, `csm_bubble.json` |
| `K-ICS.html` | Per-insurer K-ICS detail + sub-items + forward outlook | `kics_disclosure.json`, `forward_capital_latest.json`, `tier{1,2}_utilization_latest.json` |
| `IFRS17.html` | 6-panel IFRS17 dashboard (CSM waterfall / amort / P&L / NB / sensitivity / history) | `csm_waterfall*.json`, `ifrs17_panels.json`, `csm_bubble.json`, `nb_csm_ratio.embed.js`, `net_income_breakdown.json`, `disclosed_csm_multiple.json` |
| `공시보고서.html` | Static info page | (mostly text) |

Local preview: `python -m http.server 8000` from repo root, browse `http://localhost:8000/`.

---

## 2. Responsive breakpoints (committed conventions)

**M1 (foundation, 2026-05-28):** all 4 pages have `@media (max-width:640px)` block:
- header padding ↓, brand subtitle (`.hint`) hidden
- `.tabs` horizontal-scroll (nowrap + overflow-x:auto)
- `.panel` padding ↓, `.panel h2` 20→17px
- chart containers height ↓ (`.chart-container` 500→360, `.forward-chart` 420→340, `.chart-sm` 380→300, `.donut-wrap` 240→200)
- tables: `.table-container` overflow-x:auto, font 12px, th/td padding ↓
- index map: height 76vh→58vh, min-height 560→420; bubble 360

**M2 (treemap → list, 2026-05-28):** `index.html` ≤640px hides treemap (`#map{display:none}`) and shows vertical list (`#map-list`). `renderList()` mirrors `render()` inputs (same data, color scale, ratio toggle, click-through). Rows grouped by 생명보험/손해보험, sorted by 지급여력기준금액 desc.

**M3 (deferred):** donuts stacked, chart legend reposition, forward-chart legend on mobile. → `TODO_designer.md` VIS-DONUT / VIS-CHARTLEGEND.

**Full mobile pass (deferred):** `MOB-KICS` / `MOB-IFRS17` — donut row stacks, dense table → card view, panel-content / scope agreed prerequisite.

---

## 3. Chart libraries

| Library | Used for | Notes |
|---|---|---|
| **Chart.js** | Panels 2–6 in IFRS17.html (line, bar, dual-axis) | `Chart.getChart(id)` for verification |
| **ECharts** | Panel 1 (CSM waterfall), index treemap, bubble | `on('click')` for cross-nav |
| (none — vanilla) | K-ICS donuts, forward outlook line | hand-rolled inline SVG/canvas where simpler than a lib |

Don't introduce a new chart lib without owner approval.

---

## 4. Common patterns + gotchas

- **Mobile media query is `(max-width:640px)` repo-wide.** Don't introduce sibling breakpoints (`768px`, `1024px`) without owner OK — fragments the convention.
- **`@media` blocks must be self-contained.** Desktop math must not change when wrapped in mobile scope.
- **HTML single-source = root.** Don't write `templates/*.html` (those were deleted 2026-05-28). `forward_capital_simulation.py` etc. now sync to root `K-ICS.html` directly — designer must keep root-only.
- **Console error budget = 0.** Run Claude Preview after every edit, fix any error before declaring done.
- **Data JSON duplicate trap:** some scripts still write to both `data/...` and `templates/data/...`. P2 (data single-source) is on the roadmap but unfinished. If you see HTML fetching from `templates/data/`, it's an old path — change it to the single-source root location.

---

## 5. Design system (formalized 2026-06-16 via `frontend-design` skill)

> Was skeleton/TBD; now the authoritative spec. Tokens + shared chrome live in root
> [`common.css`](../../common.css), linked by all three dashboards.

### 5.1 Design tokens — single source of truth = `common.css :root`

The three dashboards already shared an identical de-facto system; it is now centralized.
**Do not redefine these in page `<style>` blocks** — reference the vars.

| Group | Tokens | Notes |
|---|---|---|
| Surface/ink | `--bg #ffffff` · `--card #f8f9fa` · `--border #e9ecef` · `--text #212529` · `--muted #6c757d` · `--ink-strong #495057` | `--ink-strong` = axis labels |
| Brand/action | `--primary #0d6efd` · `--primary-hover #0b5ed7` | ⚠ `#0d6efd` is the bootstrap-blue the owner flagged as "AI-looking". Value swap is **owner-gated** (DESIGN-V2 P1) — change the token in one place when approved, never per-page. |
| Status (financial) | `--pos #16a34a` · `--pos-soft #22c55e` · `--neg #ef4444` · `--neg-strong #dc3545` · `--warn #f59e0b` | Canonical +/△/caution. Charts still carry legacy literals; adopt progressively. |
| Type | `--font-sans` (Pretendard Variable + Korean-aware fallbacks) | `font-variant-numeric:tabular-nums` site-wide on `body`. |
| Spacing | `--sp-1 4` … `--sp-6 32` (4px base) | |
| Radius | `--r-sm 4` · `--r-md 8` · `--r-lg 12` · `--r-pill 999` | |
| Misc | `--bd` (1px border) · `--t-fast .2s` · `--maxw 1320` | mobile breakpoint = 640px (literal; `@media` can't read a var) |

**Adoption rule:** new CSS uses tokens. Existing hardcoded literals are migrated opportunistically, never in a way that changes a rendered value without owner sign-off.

### 5.2 `common.css` extraction contract

- **Linked in `<head>` BEFORE each page's inline `<style>`** → page rules win by cascade order. This makes extraction non-breaking and lets a page override any shared rule inline.
- **In common.css:** `:root` tokens, `body`, `header`, `.brand(:hover)`, `.tabs`, `.tab(:hover/.active)`, `.container`, `.select`, `.panel h2`, `.panel p`, table base (`table`,`th,td`,`th`,`th:nth-child(n+2)`,`td.subitem`), num/text utils (`.num`,`.small-muted`,`.muted`), A11y baseline.
- **Stays page-specific (do NOT hoist):** `.panel`/`.controls` (spacing differs per page), `*{box-sizing}` (present per page — index/IFRS17 lay out content-box-sensitively; a global hoist is a layout risk), every chart/component class (`.chart-container`,`.donut-*`,`.forward-*`,`.sens-*`,`#map`,`.cell`,`.li-*`,`.toggle-*`,`.swatch`,`.stub-msg`, etc.), and all `@media` blocks.
- **Non-breaking test:** every value in common.css equals the value the pages rendered on 2026-06-16. Verify after any change: `commonCssLoaded` true (no 404), 0 console errors, computed styles unchanged on all three pages at desktop + 640px.
- **Deploy note (publishing/owner):** `common.css` is a new root asset — it must ship alongside the HTML wherever they deploy (root + any templates/data mirror). Flag in the publishing handoff.

### 5.3 A11y baseline (in common.css — additive, no default-mouse visual change)

- `:focus-visible{ outline:2px solid var(--primary); outline-offset:2px }` — keyboard focus ring site-wide (shows only on keyboard nav).
- `@media (prefers-reduced-motion:reduce)` — neutralizes transitions/animations for motion-sensitive users.
- **Known gaps to extend (next A11y pass, non-blocking):** active-tab uses color only (add a non-color cue — weight/underline — once owner OKs the subtle visual change); custom toggle in index hides its `<input>` (style `.toggle-input:focus-visible + .toggle-label`); chart `<canvas>`/`#map` need `aria-label`/`role="img"` + a text summary; medium-confidence badge (`#ff9f40` on white ≈3.25:1) is sub-AA for small text.

### 5.4 Chart & responsive conventions (committed)

- **Legend density:** ≤2 series → legend top, inline. ≥3 series (NB multi-line, forward bands) → top legend desktop; on mobile prefer hiding the legend and labeling series via tooltip/axis-title to avoid overflow. Datapoint value labels: desktop on, mobile off (tooltip only) — see IFRS17 waterfall `label:{show:!isMobile}`.
- **Donut stack breakpoint:** `.donut-row` is `flex-wrap` desktop; at ≤640px donuts stack (`.donut-wrap` 240→200). The `<400px` single-column tightening is tracked as VIS-DONUT.
- **Mobile pass scope (locked by owner round3 D9):** mobile (≤640px) shows **current period only** — time-series → latest 1 point, waterfall → latest 1 bucket. Desktop windows: quarter = last 5 quarters, year = year-ends + latest partial (`selectPeriods` in IFRS17).
- **Period axis must be data-driven, label-variant-tolerant.** K-ICS solvency lookup matches both `'다. 지급여력비율 : 가 ÷ 나 × 100'` and short `'지급여력비율'` (2026.1Q uses the short form → KB etc. were dropping; fixed 2026-06-16). Never exact-match a single label string for a series that spans quarters.

### 5.5 Preserved owner decisions (LOCKED — never refactor away)

1. **Negative numbers → △ (samo)** — Korean accounting; top-priority owner directive. Lives in JS formatters (`fmtNum`/`samo`/`fmtEok`), every new table/chart must apply it.
2. **Tier1 capital donut "100%+"** — issuance ÷ recognised-cap can legitimately exceed 100%; show "100%+" with real value in tooltip.
3. **현대해상 key color = orange `#F47920`** (KEY_COLORS map).
4. **Mobile = current-period only** (see 5.4).

The `frontend-design` skill (or any redesign) must treat these four as fixed constraints.

---

## 6. Reading order for designer subagent

When invoked, read in this order:

1. This file (`TODO_designer.md`) + `docs/changelog_designer.md`
2. `docs/agents/claude-agent-designer.md` (this prompt)
3. The page(s) in scope (root HTML)
4. The master JSON schema for the data the page renders (don't modify; just understand)
5. Root `TODO.md` for cross-stage dependencies / roadmap notes
