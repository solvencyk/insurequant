---
name: a11y-audit
description: Audit insurequant's 4 deployed dashboards (index.html, K-ICS.html, IFRS17.html, 공시보고서.html) against the project's WCAG 2.1 AA accessibility baseline — contrast, colorblind-safe chart palettes, keyboard access, focus visibility, form labels. Use when adding a new page/chart/component, doing a periodic A11y pass, or when the owner asks for an accessibility check.
---

# A11y audit (insurequant designer stage)

Baseline definition, full rationale, and the 2026-07-21 audit results live in
[`docs/a11y_baseline.md`](../../../docs/a11y_baseline.md) — read that first, this
file is the repeatable **procedure**, not the spec.

## Target

WCAG 2.1 AA: 4.5:1 contrast for normal text / 3:1 for large text or UI
boundaries, no color-only meaning, keyboard-operable, visible focus, labeled
form controls. Full table in `docs/a11y_baseline.md` §1.

## Procedure

1. **Inventory colors.** `grep -n "rgb(\|#[0-9a-fA-F]\{3,6\}" <file>` per page —
   both the page's inline `<style>` and its Chart.js/ECharts config literals
   (chart colors are almost never CSS, they're JS object literals).
2. **Check text/background contrast** for every distinct foreground-on-background
   pair found (`common.css` tokens + any page-local literal) with
   `python scripts/a11y_contrast_check.py contrast "#fg" "#bg"` — don't
   hand-compute, the WCAG relative-luminance formula is easy to get subtly
   wrong by hand and this repo has been burned by that before.
3. **Check chart-palette colorblind-safety** for any palette used to
   distinguish ≥2 data series simultaneously (categorical multi-line charts,
   diverging treemap/heatmap scales):
   `python scripts/a11y_contrast_check.py cbcheck "#colorA" "#colorB"` for every
   pair in the palette. Flag pairs with `delta-RGB < 60` under either
   protanopia or deuteranopia simulation. A pair that's ALSO backed by a
   non-color cue (label, tooltip, position, symbol) is lower severity than one
   that isn't — check for that before calling it a blocker.
4. **Keyboard + focus visibility.** `grep -n "addEventListener('click'" <file>` —
   for every hit, check whether the element is a native `<button>`/`<a>`/
   `<select>`/`<input>` (fine by default) or a plain `<div>`/`<span>` (needs
   `tabindex="0"` + `role` + a `keydown` handler for Enter/Space mirroring the
   click). Then check any custom-styled control that visually hides its real
   focusable element (e.g. `opacity:0` checkboxes for toggle switches) has a
   `:focus-visible` rule targeting the *visible* sibling, not just relying on
   the sitewide `common.css` rule landing on an invisible element.
5. **Form labels.** `grep -n "<select\|<input" <file>` — every hit needs a
   wrapping `<label>`, a `<label for="id">`, or an `aria-label`.
6. **Chart screen-reader access.** Every `<canvas>` and ECharts container
   `<div>` needs `role="img"` (or `role="group"` if it has focusable children,
   e.g. a treemap with per-cell keyboard links — `role="img"` can't contain
   interactive children) + a concise `aria-label`. Static per-chart-type labels
   are an acceptable baseline; a live per-render text summary is a bigger
   follow-up, not required for a first pass.
7. **Classify every finding** into one of two buckets before touching anything:
   - **Purely additive, no rendered-value change** (adding `tabindex`,
     `aria-label`, a `keydown` handler, a missing `common.css` `<link>`, a new
     `:focus-visible` rule) → fix directly, it's always safe.
   - **Changes something an existing user already sees** (any `common.css`
     token value, any literal hex/rgb color already in use, a chart palette
     swap, a color-only cue becoming a color+shape cue) → **do not auto-fix**.
     `common.css`'s own header says token values are owner-gated ("Palette
     swap ... is owner-gated — do NOT change token VALUES here without
     sign-off"); the same rule applies to any page-local literal that's
     already rendering. List it for owner review instead.
8. **Verify in Claude Browser preview**, desktop (1280px) + mobile (375px):
   0 console errors, and for any newly-keyboard-accessible element, dispatch a
   `KeyboardEvent('keydown',{key:'Enter'})` and confirm it produces the same
   effect as a click (`document.activeElement.focus()` is unreliable in a
   headless/automated tab — the tab often lacks OS-level window focus, so
   `document.hasFocus()` returns false even though the DOM wiring is correct;
   dispatching the event directly and checking the resulting side-effect,
   e.g. `window.location.href`, is the reliable check).
9. **Write up**: append to `docs/a11y_baseline.md` §2 (fixed / owner-review
   queue), update `docs/agents/claude-agent-designer.md` §5.3, log in
   `TODO_designer.md` + `docs/changelog_designer.md`.

## Known repo-specific traps

- `common.css` is linked in 3 of the 4 pages historically — always check the
  4th (`공시보고서.html`) hasn't drifted; it's the one most likely to be
  edited standalone and forgotten.
- The `.subtoggle` (+/− expand button) pattern is already a real `<button>`
  with `aria-expanded` — don't re-flag it.
- The site's △ (samo) negative-number convention already double-encodes sign
  independent of color on every value that uses it — a red/green pair backed
  by △ is lower severity than one that isn't. Check for `△` in the same
  formatter before flagging a color pair as color-only.
- Chart color literals are duplicated per-file (no shared JS palette module),
  so a palette fix found in one file doesn't propagate — grep all 3
  chart-bearing pages separately.
