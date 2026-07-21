# A11y baseline + audit (2026-07-21)

> Ordered by [inbox/designer/20260721T0233Z](../inbox/_resolved/20260721T0233Z__owner__MULTI__adopt_a11y_audit_baseline.md) (`ui-ux-pro-max` external skill reviewed and passed on — see §4). Scope: baseline definition + audit + owner-review queue for the 4 deployed pages (`index.html`, `K-ICS.html`, `IFRS17.html`, `공시보고서.html`). Fixes beyond the low-risk ones below wait for owner sign-off per the order.

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

### 2b. Owner-review queue (touches an existing rendered value or needs real content authoring — not auto-fixed)

| # | File | Finding | Severity | Why not auto-fixed |
|---|---|---|---|---|
| 7 | `common.css` `--muted` | `#6c757d` on `--card` (`#f8f9fa`) = **4.45:1**, just under the 4.5:1 text threshold (on plain white it's 4.69:1, fine) | Low | `--muted` is used everywhere (`.panel p`, `td.subitem`, chart axis labels via JS `getPropertyValue('--muted')`, inactive tab text); nudging the token darker changes a rendered value sitewide — explicitly owner-gated (`common.css` header: "do NOT change token VALUES here without sign-off") |
| 8 | `index.html` bubble-legend | `● 손해` label: `color:#16a34a;font-weight:700` on white, no explicit large font-size = **3.30:1**, fails normal-text AA (passes the 3:1 large-text/UI threshold, but this isn't reliably "large text") | Low-Medium | Literal hex, not a token — same "rendered value" gate |
| 9 | `K-ICS.html` donut center / `IFRS17.html` missing-data cells | `#adb5bd` "no data" placeholder (`—`) on white = **2.07:1** | Low | Arguably incidental (a dash, not information-bearing text) but still worth a token if adopted later |
| 10 | `K-ICS.html` teal/pink series pair (`rgb(75,192,192)` / `rgb(255,99,132)`) used for 지급여력비율 vs 기본자본비율 everywhere | Simulated under protanopia/deuteranopia: **stays distinguishable** (ΔRGB grows to 113–143 under simulation — luminance/blue-channel carries it even though hue shifts). Documenting as **checked, no action needed**, not a violation. | — | — |
| 11 | `IFRS17.html` `NB_LINE_COLORS` 6-color categorical palette (`#0d6efd,#198754,#fd7e14,#6f42c1,#20c997,#dc3545`) for the NB/CSM-multiple multi-line chart | Under deuteranopia: orange↔red (ΔRGB 51) and purple↔teal (ΔRGB 39) become close; under protanopia: orange↔red (ΔRGB 52) | Medium | Legend + tooltip already provide a non-color way to identify a series, so this degrades rather than breaks usability. Palette is a rendered value (owner-gated design-system decision), and a colorblind-safe 6-hue categorical swap is a real design choice, not a token nudge |
| 12 | `index.html` treemap swatch + bubble swatch diverging gradients (`#7f1d1d→#ef4444→#fca5a5→#34d399→#16a34a→#14532d` and `#7f1d1d→#f59e0b→#84cc16→#14532d`) — red↔green diverging scale for solvency ratio | Endpoint contrast **drops** under simulation (normal 3.04:1 → ~1.1–1.3:1 under protanopia/deuteranopia for the first scale) — the classic red-green diverging-scale problem | Medium | Every cell already has a `title` tooltip with the exact number, and cells above a size threshold show the numeric ratio as text — so the color is reinforced, not the only channel. Still, a colorblind user scanning the treemap by color alone (its main value-prop) won't reliably tell "good" from "bad" at a glance. Recommend considering a red↔blue diverging scale in a future DESIGN-V2 pass; this is a bigger design-system decision than this order's scope |
| 13 | `index.html` active-tab uses color only (`.tab.active{background:var(--primary)}`) for **sighted** users | Low | Screen-reader side now mitigated by the `aria-current="page"` fix in §2a row 6; the remaining gap is purely visual (no non-color cue for sighted keyboard/low-vision users who don't rely on a screen reader). Already known (`claude-agent-designer.md` §5.3 pre-existing note) — still owner-gated pending a subtle visual-change (weight/underline) sign-off |
| 14 | 10 chart `aria-label`s added in §2a are **static** (fixed Korean text per chart type), not dynamic per selected company/values | Low | A screen-reader user gets "this is the CSM waterfall chart" but not the live numbers (sighted users get those from hover tooltips, which SR users can't reach on a `<canvas>` either). A live-region or generated text-summary per render is a real content-authoring task, out of scope for this pass — flagged for a follow-up ticket, not attempted here |

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
