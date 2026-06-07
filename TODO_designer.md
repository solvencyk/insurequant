# Insurequant Designer TODO (Stage 5)

Last updated: 2026-05-31 (split out of root `TODO.md`).

Stage 5 — **designer**: HTML structure, styling, responsive breakpoints, A11y, chart layout. Publishing ([`TODO_publishing.md`](TODO_publishing.md)) owns master JSONs; designer only reads them and decides how they render.

**Stage files**
- Prompt: [`docs/agents/claude-agent-designer.md`](docs/agents/claude-agent-designer.md) (skeleton)
- Changelog: [`docs/changelog_designer.md`](docs/changelog_designer.md)
- This file: open designer work + done archive

Session start: read this file + `claude-agent-designer.md` + the page(s) in scope (root HTML files).

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

---

## 🚧 Open designer work

### MOB-KICS — K-ICS.html full mobile layout

Status: **deferred**. M1 foundation only (header/tabs/table scroll, chart heights ↓).

Full pass blocked on panel content/scope agreement. When unblocked, address:
- [ ] Donuts stacked vertically (currently row, cramped <400px)
- [ ] Forward-chart legend reposition (overflows on mobile)
- [ ] Dense table → card view (가/나/다 sub-items)

### MOB-IFRS17 — IFRS17.html full mobile layout

Status: **deferred**. M1 foundation only.

Defer full pass until display-metric scope agreed (Panel 1–6 mobile policy: which to keep, which to collapse, which to swap for alternate viz).

### VIS-DONUT — K-ICS donut row stacks on phones

Status: **todo**.

- [ ] `.donut-cell` cramped <400px → stack vertically (`flex-direction: column` at narrow breakpoint, or sub-media query `<400px`)
- [ ] Verify ratio labels still legible after stack

### VIS-CHARTLEGEND — chart legend/axis density on mobile

Status: **todo**.

- [ ] Chart.js legends overflow narrow widths
- [ ] Options: (a) hide legend on mobile + force tooltip, (b) reposition bottom, (c) abbreviate labels
- [ ] Affects: K-ICS forward outlook line, IFRS17 Panel 2/3/4/6, index bubble

### M3 — chart fine-tuning (optional follow-up to M1/M2)

Status: todo. Roll up of above two + miscellaneous.

- [ ] K-ICS 도넛 2개 세로배치 (= VIS-DONUT)
- [ ] Forward 라인 범례 위치 (= VIS-CHARTLEGEND subset)
- [ ] 차트 미세조정 across pages

### Panel 7 — 원천지표 카드 (CSM 잔액·상각액·NB CSM 직접 노출)

Follow-up from 2026-05-28 panel cleanup. Replaces removed 파생 KPI 카드 4개 + BS 스냅샷 패널 with raw-metric cards.

- [ ] Card design (one row of 4: CSM 잔액 / CSM 상각액 / NB CSM / NB CSM 배수)
- [ ] Per-company selector reuse
- [ ] Data source: existing `csm_waterfall.json` + `csm_bubble.json`

### INDEX-BUBBLE-V2 HTML side — 4축 bubble rendering

Publishing ships the data (`TODO_publishing.md` INDEX-BUBBLE-V2). Designer ships the ECharts spec:

- [ ] 4축 mapping: X=당기순이익 / Y=CSM 잔액 / size=신계약 CSM / color=신계약 CSM 배수
- [ ] Mobile rendering: 4축 → simplified (e.g. bar 또는 list with sort options)
- [ ] Click → cross-nav (existing pattern)

### F17 Panel 3 — Tier2 LOB drill-down rendering (when publishing ships Tier2 JSON)

Publishing currently has Tier1 4-bar in production. Tier2 (LOB 장기/자동차/일반 stacked) waits on parser F17 decision + publishing assembly.

- [ ] Stacked bar / waterfall design (손보만, LOB visible)
- [ ] 생보 alt-rendering (장기 전사 fallback)
- [ ] Caption variant per-company taxonomy (장기/자동차/일반 vs 보장성/물보험/저축성)

---

## 🗂️ Conventions reference

**Responsive breakpoints**
- M1 foundation: `@media (max-width:640px)` on all 4 pages. Header/tabs/chart heights/table scroll.
- M2: index.html ≤640px swaps treemap → vertical list (`renderList()` mirrors `render()`).
- M3 (this TODO): donut stack + legend reposition + chart fine-tuning.

**Chart libraries (committed)**
- Chart.js: IFRS17 Panels 2–6
- ECharts: Panel 1 (CSM waterfall), index treemap, bubble

**Page roster (root single-source since 2026-05-28)**
- `index.html` — market map + IFRS17 quadrant + bubble
- `K-ICS.html` — per-insurer detail + sub-items + forward outlook
- `IFRS17.html` — 6-panel dashboard
- `공시보고서.html` — static info

**Local preview:** `python -m http.server 8000` from repo root.

---

## 📦 Done — recent (designer-scoped)

| ID | Task | Done | Notes |
|----|------|------|-------|
| ~~F-PL-WF~~ | Panel 3 당기순이익 bridge waterfall (PL_breakdown.json) | 2026-06-07 | First cut. 5-bar bridge 보험손익→투자손익→영업외→(−)법인세→당기순 (exact reconcile, 손보+생보). 단위 백만원. 연도=`값`(YTD, latest 4Q) / 분기=`값_당분기` (both work). Reuses #wfPeriod. ECharts `#chartPl`. **TODO(owner): company-name canonicalization** (PL 삼성생명보험 vs dropdown 삼성생명; plResolve fuzzy stopgap, 케이비라이프↔KB라이프 gaps). Removed orphan ni wiring. Preview-verified (getOption), console 0. Report `artifacts/designer/panel3_pl_bridge_waterfall_20260607.md` |
| ~~F-WF-WINDOW~~ | Panel 1 windowed CSM waterfall (company × 연도/분기) | 2026-06-07 | New long-format `CSM_waterfall.json` (23사, 억원, YTD). 연도 mode = trailing 4 buckets, 18-bar expanded (기초 → 연도별 신계약·이자·가정/경험·상각 → 기말). 분기 mode stubbed (`WF_QUARTER_READY=false`) until 당분기 table. Mobile dataZoom. K-ICS selector methodology reused. Preview 375/1280 verified, console 0. Report `artifacts/designer/panel1_windowed_csm_waterfall_20260607.md` |
| ~~M1~~ | Mobile responsive foundation (4 pages) | 2026-05-28 | `@media (max-width:640px)` on all 4. Header/tabs/table scroll, chart heights ↓. Desktop math unaffected (≤640px scoped). Claude Preview 375px/1280px verified |
| ~~M2~~ | index.html treemap → vertical list on phones | 2026-05-28 | `renderList()` mirrors `render()` (same data, color, toggle, click-through). Rows grouped 생명/손해, sorted ratio desc, bar/color = ratio |
| ~~INDEX-TREEMAP-CLEAN~~ | Desktop treemap label cleanup (size-aware) | 2026-05-28 | Dropped 기준 XXX meta line + .meta CSS. Name shown if cell ≥46×60px, ratio if ≥26×44px. `.cell justify-content:flex-start;gap:3px` |
| ~~INDEX-LIST-SORT~~ | Mobile list sort fix | 2026-05-28 | Changed from ratio desc → 지급여력기준금액(required) desc. 삼성생명 top, 라이나 9th (was top at 343%) |
| ~~IFRS17-PANEL-CLEAN~~ | IFRS17 패널 정리 (KPI 카드 4개 + BS 스냅샷 panel 제거) | 2026-05-28 | Removed Panel 5 KPI 카드 + Panel 6 BS 스냅샷 표 → `docs/archived_metrics.md` archive. Panels renumbered 1–6 (wf/amort/pl/nb/sens/hist). Generators kept |
| ~~F6-HTML~~ | F6 yearly CSM amort Panel 2 HTML | 2026-05-28 | Desktop 10y / mobile 5y matchMedia(max-width:640px). Coarse companies fall back to 4-bucket. Re-render on breakpoint change. `Chart.getChart` verified |
| ~~F17-PANEL3~~ | Panel 3 clean 4-bar swap | 2026-05-30 | Was raw-table last-column 12-row horizontal bar dump. New: 보험손익 / 투자손익 / 영업외 → 당기순이익 + 보종별 caption. 콘솔 에러 0 |
| ~~P1-HTML-SINGLE~~ | HTML single-source refactor | 2026-05-28 | templates/*.html 4개 삭제. Root sole copy. forward_capital_simulation.py syncs into root K-ICS.html directly |
| ~~P4-DEAD-CDN~~ | index.html dropped unused xlsx.full.min.js CDN | 2026-05-28 | ~900KB. Zero `XLSX.` usage. 817→816 lines |
| ~~CONSOLE-CLEAN~~ | Debug console.log cleanup across pages | 2026-05-28 | Pre-mobile-pass tidy |
| ~~INDEX-C12~~ | index treemap + IFRS17 quadrant | done | Post-transition default for items 27/28 |
| ~~KICS-HTML-SUB~~ | K-ICS.html sub-items + transition toggle | done | + JSON sync (root single-source) |
| ~~F1-HTML~~ | index.html → IFRS17 cross-nav | done | `fcdd544`. ECharts on('click') → URL param + auto-select |

---

## Reading order for designer subagent

1. This file (`TODO_designer.md`) + [`docs/changelog_designer.md`](docs/changelog_designer.md)
2. [`docs/agents/claude-agent-designer.md`](docs/agents/claude-agent-designer.md)
3. Root HTML page(s) in scope
4. Master JSON schema (publishing's output) for the panel you touch — read-only
5. Root [`TODO.md`](TODO.md) for cross-stage roadmap notes

---

## Hand-off

- **From publishing**: notification that a master JSON changed (`manual_html_edit` warn) or that a new field needs rendering.
- **To human**: designer never pushes. Hand off to publishing for the commit message + push recommendation.
