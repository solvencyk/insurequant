# Insurequant Changelog — Designer Stage

Stage 5 of 5 in the workflow split. See `CLAUDE.md` for the full 5-stage index.

**Scope:** HTML structure / styling / responsive breakpoints / chart layout / A11y. Master JSON content is **publishing** ([`changelog_publishing.md`](changelog_publishing.md)) — designer reads them but does not modify.

**Cross-stage history:** `docs/claude-changelog.md`.
**This file:** entries scoped to designer work only.

---

## 2026-05-31 -- Designer stage created (split from publishing)

User observation: HTML structure/styling is a different kind of work from data assembly. Split out as its own stage. Publishing now strictly owns master JSONs; designer strictly owns HTML.

- New prompt: `docs/agents/claude-agent-designer.md` (skeleton with Contract + responsive conventions + chart library inventory)
- New TODO/changelog created from root TODO items: MOB-KICS / MOB-IFRS17 / VIS-DONUT / VIS-CHARTLEGEND + M3 chart fine-tuning + Panel 7 원천지표 카드 + INDEX-BUBBLE-V2 HTML side + F17 Tier2 LOB rendering.
- Done archive imported: M1 (responsive foundation) / M2 (treemap → list) / index treemap cleanup + list sort / IFRS17 panel pruning / F6 yearly amort HTML / F17 Panel 3 swap / P1 HTML single-source refactor / P4 dead CDN drop / console cleanup / INDEX-C12 / KICS-HTML-SUB / F1 cross-nav.

---

## 2026-05-30 -- Panel 3 clean 4-bar swap (data from publishing F17-T1)

Replaced the raw-table last-column 12-row horizontal bar dump with a clean 4-bar 당기순이익 decomposition:

- 보험손익 (+)
- 투자손익 (+)
- 영업외
- → 당기순이익 (강조색)

`h2 '3) 당기순이익 분해 (보험손익·투자손익)'`. 보험금융 + 보종별 caption. Browser verified (삼성화재 / 현대 / 한화 렌더 정상). 생보 graceful stub. 콘솔 에러 0.

Data source: publishing's `data/dart/viz/net_income_breakdown.json` (Tier1 10/10 손보).

---

## 2026-05-28 -- IFRS17 패널 정리 + F6 yearly amort Panel 2

**F6 HTML side:** yearly bar chart, desktop 10y / mobile 5y (`matchMedia(max-width:640px)`); coarse companies fall back to 4-bucket view; re-render on breakpoint change. Verified via `Chart.getChart`: DB생명 desktop=10 bars, mobile-load=5 bars; 삼성생명 (coarse)=4-bucket fallback. No console errors.

**Panel pruning:** removed Panel 5 "Downstream KPI 카드" (4 proxy KPIs) + Panel 6 "BS 스냅샷 표" from `IFRS17.html` (template + renderCompany blocks + PATHS/payload/ix/boot wiring + `.kpi-*` CSS + now-orphan `renderMatrixTable`). Generators kept (`downstream_kpis.json` still feeds the bubble's closing CSM — publishing side). Definitions preserved in `docs/archived_metrics.md`.

Panels renumbered 1–6 (wf / amort / pl / nb / sens / hist); intro "7패널" copy fixed.

Follow-up (now in TODO_designer.md): **원천지표 카드 신설** (CSM 잔액·상각액·NB CSM 직접 노출, 제거한 파생 KPI 대체) — Panel 7.

---

## 2026-05-28 -- index treemap text cleanup + mobile list sort

User feedback: desktop treemap company labels overlapped/clipped in small tiles; 지급여력기준금액 text redundant (tile size already encodes it).

- Dropped the "기준 XXX" meta line from every cell (removed `.meta` CSS + JS)
- Size-aware labels: name shown only if cell ≥46×60px, ratio only if ≥26×44px; tiny cells show color only (no clipped text)
- `.cell` now `justify-content:flex-start;gap:3px` (clusters name+ratio top-left)
- Mobile list `renderList`: sort changed from ratio desc → **지급여력기준금액(required) desc**, so big insurers (삼성생명…) top, matching the treemap; bar/color still encode ratio. (User: 라이나 343% sitting on top felt off.)
- Verified via Preview: desktop labels clean & non-overlapping; mobile 삼성생명 top / 라이나 9th; zero console errors

---

## 2026-05-28 -- M2 mobile responsive (treemap → vertical list)

The treemap can't fit 30+ insurers legibly on a 375px screen (small tiles clipped). Per research, the fix is a *different* presentation on mobile, not shrinking. index.html now swaps the treemap for a vertical list below 640px.

- New `#map-list` container + `.li-*` styles (name + colored magnitude bar + ratio%)
- New `renderList(sector)` JS: mirrors `render()` inputs — same `GROUPED` data, `colorForRatio()` scale, ratio toggle (kics/basicCapital), and click → `K-ICS.html?company=...`. Rows grouped by 생명보험/손해보험, sorted ratio desc, bar width = ratio/maxRatio
- Called at the end of `render()`, so every redraw updates both views; CSS @media decides which is visible
- `@media (max-width:640px)`: `#map{display:none}` + `.map-list{display:block}` (replaced M1's map height tweak)

Verified via Claude Preview: mobile 375px shows clean sorted list (라이나 343% … 한화 157%), all insurers legible; desktop 1280px treemap unchanged; zero console errors.

---

## 2026-05-28 -- M1 mobile responsive foundation (4 pages)

User asked to make the site look good on phones (index treemap "와장창 찌그러짐"). Audit found **zero `@media` queries** across all 4 pages — viewport tag present but no responsive breakpoints, so desktop layout was forced onto phones.

Added identical `@media (max-width:640px)` block to index/K-ICS/IFRS17/공시보고서.html:
- header padding↓, brand subtitle (`.hint`) hidden, container padding 16→10px
- `.tabs` horizontal-scroll (nowrap + overflow-x:auto) so tabs never wrap/overflow
- `.panel` padding↓, `.panel h2` 20→17px, `.select` smaller
- chart containers height↓ (chart-container 500→360, forward-chart 420→340, chart-sm 380→300); donut-wrap 240→200
- tables: `.table-container` overflow-x:auto, font 12px, th/td padding↓
- index map: height 76vh→58vh, min-height 560→420; bubble 360
- All scoped under ≤640px → desktop mathematically unaffected

Verified via Claude Preview (python http.server :8765): mobile 375px — tabs fit one row, big insurer tiles legible; desktop 1280px — unchanged. Data loads fine over http (12,795 rows, no console errors).

---

## 2026-05-28 -- HTML single-source refactor (P1 + P4 — designer side)

Frontend-fundamentals audit (per user's "비개발자 바이브코더" video). Diagnosed 5 정합성 issues; fixed P1 (HTML duplication) + P4 (dead dependency) this round.

**Root cause:** `K-ICS.html` existed in both root and `templates/` and had **drifted** — only line 171 (`window.FORWARD_DATA` inline blob) differed. `forward_capital_simulation.py` (publishing side) wrote only to `templates/K-ICS.html`, so the deployed root copy served stale forward-capital numbers. index/IFRS17/공시보고서 copies were still identical.

**P1 — single source = root:**
- `cp templates/K-ICS.html → K-ICS.html` (root now carries fresh data)
- `git rm templates/{index,K-ICS,IFRS17,공시보고서}.html` (4 HTML mirrors removed). templates/ now holds only data JSONs
- (Publishing side: `forward_capital_simulation.py` sync path updated)
- Local preview now: `python -m http.server 8000` from repo root (was `-d templates`)

**P4 — dead dependency:** index.html dropped unused `xlsx.full.min.js` CDN (~900KB, never called; only the `<script>` tag existed, zero `XLSX.` usage). 817→816 lines.

**Deferred:** data-JSON duplication (templates/data/...) = future P2 (publishing-side cleanup). Remaining HTML structure todos: P3 shared CSS/nav → assets/common.css; P5 K-ICS inline data → external JSON+fetch.

---

## Older entries

Pre-2026-05-28 HTML/viz design entries are in the compressed historical archive of root `docs/claude-changelog.md` ("## Historical archive (compressed)"):

- IFRS17.html 6-panel dashboard layout (initial)
- K-ICS.html Phase 4 (자본성증권 도넛 + Forward Outlook 라인 dual-axis)
- index.html treemap (initial Phase 3 wave)
- K-ICS sub-items + transition toggle HTML
