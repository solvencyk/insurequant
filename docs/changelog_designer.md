# Insurequant Changelog — Designer Stage

Stage 5 of 5 in the workflow split. See `CLAUDE.md` for the full 5-stage index.

**Scope:** HTML structure / styling / responsive breakpoints / chart layout / A11y. Master JSON content is **publishing** ([`changelog_publishing.md`](changelog_publishing.md)) — designer reads them but does not modify.

**Cross-stage history:** `docs/claude-changelog.md`.
**This file:** entries scoped to designer work only.

---

## 2026-06-07 -- Panel 3 당기순이익 bridge waterfall (PL_breakdown.json)

Replaced Panel 3 (old Chart.js 손보-only 당기순이익 분해 from `net_income_breakdown.json`)
with a CSM-style **bridge waterfall** from new root `PL_breakdown.json`, reusing Panel 1's
보험사 + 기준(연도/분기) controls. First cut — owner to refine details.

- 5-bar bridge (exact reconciliation verified, 손보+생보): **보험손익(1) → 투자손익(17) →
  영업외손익(21) → (−)법인세(23) → 당기순이익(24)**. 단위 백만원, 축 조원, ECharts (Panel 1 technique).
- Source has **both YTD(`값`) and 당분기(`값_당분기`)** → 분기 mode works now (unlike CSM):
  연도=latest `*.4Q` via `값`; 분기=latest Q via `값_당분기`. Shared #wfPeriod drives both panels
  (분기 → CSM stubs, PL shows quarterly).
- `PATHS.plx` (root + data/ fallback), `ix.plx` = company→quarter→항목번호→{y,q}.
  Template canvas→div `#chartPl`; `destroyCharts` wf+pl now ECharts(dispose), amort/nb/hist Chart.js.
- **Company-name mismatch flagged:** PL uses 삼성생명보험/미래에셋생명보험/코리안리재보험/KB라이프생명
  (vs dropdown 삼성생명/…/코리안리/케이비라이프생명보험). `plResolve()` fuzzy-matches (substring);
  케이비라이프↔KB라이프 still gaps → stub. Publishing to canonicalize names.
- Removed orphaned `ni`(net_income_breakdown) wiring (my-change orphan). Pre-existing dead
  `payload.pl`/`ix.pl` (insurance_pl_breakdown) left untouched.
- Verified via ECharts getOption + canvas dims (screenshot tool hung renderer-side):
  현대해상 FY2025 (396,111→…→561,106 reconciles), 현대해상 2026.1Q 당분기, 삼성생명→삼성생명보험
  resolve, 삼성화재 mobile, 처브라이프 stub. **0 console errors** both breakpoints.
- Report: `artifacts/designer/panel3_pl_bridge_waterfall_20260607.md`.

---

## 2026-06-07 -- Panel 1 windowed CSM waterfall (company × 연도/분기)

Replaced Panel 1's single fixed 2024 year-end waterfall with a **company × period
windowed** waterfall, mirroring `K-ICS.html` selector methodology.

- New source: root `CSM_waterfall.json` (long-format: 원수사명/항목번호/항목명/공시분기/값,
  23사 × 2023.1Q~2026.1Q, **단위 억원**, YTD/연 누계). Wired as `PATHS.wfx` (root primary
  + `data/dart/viz/` fallback), indexed `ix.wfx` = company→quarter→항목번호→값.
- **연도 mode (shipped):** trailing 4 buckets (latest period + prior year-ends), expanded
  to 18 bars — 기초 CSM → 연도별 신계약·이자·가정/경험·상각 → 기말 CSM. Axis in 조원,
  tooltips in 조+억. Component reconciliation + year-end chain verified against data.
- **분기 mode (stubbed):** UI present; `WF_QUARTER_READY=false` shows "당분기 데이터 준비 중"
  because the file is YTD and can't be decomposed per-quarter. Flip flag when 당분기 table lands.
- Old stages-based `renderWfEcharts` removed (my-change orphan). Company dropdown = union of
  legacy 28사 + new 23사, so legacy-only insurers still list and Panel 1 stubs gracefully.
- Mobile: ECharts `dataZoom` (inside+slider) on the 18-bar chart, defaults to latest ~2 groups;
  `@media (max-width:640px)` convention unchanged, desktop math untouched.
- Verified via Claude Preview at 1280px + 375px (삼성생명 10.7조→13.6조, 현대해상, DB생명,
  분기 stub, 라이나 missing-data stub): **0 console errors**.
- Report: `artifacts/designer/panel1_windowed_csm_waterfall_20260607.md`.
- Hand-off to publishing: relocate `CSM_waterfall.json` → `data/dart/viz/`; flip
  `WF_QUARTER_READY` when per-quarter table ships.

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
