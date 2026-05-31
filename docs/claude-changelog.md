## 2026-05-31 — Parser stage split out

Parser 전용 신규/이력 항목은 [`docs/changelog_parser.md`](changelog_parser.md) 로 분리됨. 이 root changelog는 cross-stage 항목만 (gathering / pushing / refactor / cross-stage viz / 폴더 정리). 이번 split 으로 옮긴 entry:

- **2026-05-31** F17 Tier2 LOB 9/11 사 확장 + IR cross-check (3사: 메리츠 ok / 삼성 일반 +246% / DB 자동차 sign flip) — 결정 대기
- **2026-05-30 (b)** F17 Tier2 LOB 방법론 수정 (position-based 컬럼 식별, rollforward 표 제외, Tier1 연결 우선)
- **2026-05-30** F17 손보 당기순이익 분해 Tier1 10사 / Tier2 1사 (현대 검증)
- **2026-05-30** IR factsheet + 손보 disclosed/derived NB CSM 배수 (삼성화재 / DB / 한화손보 / 현대)
- **2026-05-29** 삼성생명·미래에셋 상품군 분리공시 합산 + 소계 이중계상 제거 (FY anchor 정정)
- **2026-05-29** `<TE>` data-cell 미파싱 root cause (이전 "원본에 없음" 진단 철회)
- **2026-05-29** Panel 5 sensitivity rowspan + 한화 2023.4Q dip (continuity tiebreak)
- **2026-05-29** NB CSM Samsung 사망 misparse fix (parser side; validation gate는 changelog_validation 2026-05-29)
- **2026-05-29** CSM 시계열 prior-period decontamination + per-quarter new-business
- **2026-05-25** IFRS17 B5 K-ICS sensitivity appendix + multi-period batch
- **2026-05-25** IFRS17 historical 13Q ingest (parser promote step)
- Historical archive 2026-05-25 / 05-24 parser items (RED reduction, KICS parser progression, IFRS17 bootstrap)

## 2026-05-31 — Validation stage split out

Validation 전용 신규/이력 항목은 [`docs/changelog_validation.md`](changelog_validation.md)로 분리됨. 같은 날 추가된 **DART↔IR cross-source 3개 룰**(`CSM_WATERFALL_DART_VS_IR` / `SEGMENT_INSURANCE_INCOME_DART_VS_IR` / `CSM_BREAKDOWN_DART_VS_IR`)도 그쪽 참고. Cross-stage 의존: F18 (parser/gathering이 `data/ir/<period>/parsed/<KR>.json` 정형 JSON delivery 시 룰 자동 활성화).

## Stage entries moved out

- **Downloader**: (j) Reorg #2 ~ (c) F2 v3 KIDI crawler — all 2026-05-30 downloader work → [`docs/changelog_downloader.md`](changelog_downloader.md) under the same headings.
- **Parser**: 2026-05-31 F17 9/11 / 2026-05-30 (b) Tier2 방법론 / 2026-05-30 Tier1+Tier2 PoC / 2026-05-30 IR disclosed/derived / 2026-05-29 product-segmented + `<TE>` + rowspan + de-contam / 2026-05-25 B5 appendix + historical promote → [`docs/changelog_parser.md`](changelog_parser.md).
- **Validation**: 2026-05-31 cross-source rules, 2026-05-30 validation prompt 초안, 2026-05-29 Plausibility gate, 2026-05-25 rules 9+10 / RED reduction 99→2 / Tier-2 reconcile, 2026-05-24 KICS-VALIDATE harness initial → [`docs/changelog_validation.md`](changelog_validation.md).

This root changelog retains cross-stage entries only (gathering / pushing / refactor / viz / cross-stage validation+parser pointers).

See `CLAUDE.md` for the 5-stage workflow split index.

## 2026-05-30 -- data/ifrs17 -> data/dart 폴더 리네임 + Panel 3 viz 교체 (F17 gathering 절반)

**폴더 리네임 data/ifrs17 -> data/dart (완료·검증).** 사용자 지시대로 현행 dup `data/dart`(FY_Q 복사본) 삭제 후 `data/ifrs17` -> `data/dart` 실제 리네임. 코드 repoint: `data/ifrs17` 및 `"data" / "ifrs17"` 경로형만 치환(35개 파일) — `src/ifrs17` 모듈/`IFRS17.html` 파일명/`from src.ifrs17`는 불변. `config.py` 중앙경로 `root/"data"/"dart"`, `templates/data/ifrs17`->`templates/data/dart`, 정규화 JSON self-ref 포함. 잔여 `data/ifrs17` 참조 0개. viz 빌드(panels/waterfall) 재실행 정상(28사, 회귀 0). **폴더구조 개편(공시분기>회사) 차후** 보류.

**Panel 3 viz 교체 (F17 gathering 절반).** IFRS17.html Panel 3을 기존 '원시표 마지막열 12행 horizontal bar 덤프' 에서 **클린 4-bar 당기순이익 분해** (보험손익 / 투자손익 / 영업외 → 당기순이익, 당기순이익 강조색) + 보험금융·보종별 caption 으로 교체. h2 '3) 당기순이익 분해 (보험손익·투자손익)'. 브라우저 검증: 삼성화재 / 현대 / 한화 렌더 정상, 생보 graceful stub, 콘솔 에러 0.

(F17 parser 절반 — Tier1 10사 OK / Tier2 1사 → 4사 → 9/11 사 확장, 2026-05-30·30b·31 — 은 [`docs/changelog_parser.md`](changelog_parser.md) 로 이동. 같은 날 IR factsheet 전사 수집 + 손보 disclosed/derived NB CSM 배수 파싱 [삼성화재 / DB / 한화손보 / 현대] 도 동일 changelog 로 이동.)

[parser orphan block removed — see changelog_parser.md "2026-05-30 — IR factsheet 전사 수집".]

[parser orphan block removed — see changelog_parser.md "2026-05-29 — 삼성생명·미래에셋 합계-vs-CSM 컬럼 식별".]

[parser orphan block removed — see changelog_parser.md "2026-05-29 — CSM 시계열 결측 진짜 원인: `<TE>` 데이터셀 미파싱".]

[parser orphan block removed — see changelog_parser.md "2026-05-29 — Panel 5 sensitivity rowspan fix + 한화 2023.4Q dip".]

[parser orphan block removed — see changelog_parser.md "2026-05-29 — NB CSM multiple Samsung 사망 misparse fix". Validation 측 plausibility gate 는 changelog_validation.md 동일 날짜 entry.]

[parser orphan block removed — see changelog_parser.md "2026-05-29 — CSM 시계열 (Panel 6) prior-period de-contamination + per-quarter new-business".]

## 2026-05-29 -- F11 DONE: foreign-affiliate life insurers fully in IFRS17 dashboard

User pushed to start F11 (add 5 foreign-affiliate life insurers to IFRS17), then approved full viz integration. Result: IFRS17 cohort 23→28 (생보 13→18), all 5 rendering in the dashboard + index bubble. Browser-verified, zero console errors, zero regression to the existing 23.

**Viz integration was glob-driven — almost no HTML change.** The builders enumerate `data/dart/extracted/*.json` (panels: `*_csm.json` / `*_insurance_pl_mvp.json` / `*_sensitivity_mvp.json`; waterfall: `*_measurement.json`) and IFRS17.html builds its company selector from `wf.companies`, index.html bubble from `csm_bubble.json`. So producing the standard artifacts auto-grew the selector (28 options) and the bubble (28 points). nb + hist panels stub gracefully for the 5 (no IR premium mapping; not in the 23-co 13Q history cohort).

- `scripts/ifrs17_ingest_audit_annual.py`: extended to also run measurement / insurance_pl / sensitivity extractors on the already-fetched audit-report XMLs (same artifact names the per-tier batch scripts emit). Re-run: 5/5 ok (meas 8-25, pl_mvp 1-10, sens_mvp 16-41 tables).
- Re-ran `viz_build_csm_waterfall.py` (28 co), `viz_build_ifrs17_panels.py` (pl 28/28, sens 18/28), `viz_build_csm_bubble.py` (csm 28, the 5 grey = no NB multiple).

**3 safe waterfall-builder fixes** (`viz_build_csm_waterfall.py`) verified zero-regression vs 23-co snapshot — detail in [`docs/changelog_parser.md`](changelog_parser.md) "2026-05-29 — F11 waterfall-builder 3 safe fixes".

Final waterfall status for the 5: 메트라이프 / AIA / 처브라이프 / 하나생명 **ok**; 라이나생명 **partial** (rollforward has no matched amort row; Panel 2 amort schedule is clean from csm.json).

**Feasibility (data half, earlier this session):** all 5 file no pblntf_ty=A periodic report, but their standalone DART **감사보고서** (2024.12, pblntf_ty="F") carries the same IFRS17 보험계약 주석 with a CSM amort schedule. The **existing `csm_extractor` parses all 5 unchanged** (form A, score 5-6; year-bucket portfolio tables, Non-Par 유배당/무배당, 천원).

| insurer | corp_code | 2024.12 감사보고서 rcept_no | CSM tables |
|---|---|---|---|
| 라이나생명보험 | 00504232 | 20250409002702 | 6 |
| 메트라이프생명보험 | 00171104 | 20250402000865 | 3 |
| 에이아이에이생명보험 | 01295517 | 20250401000094 | 6 |
| 하나생명보험 | 00187123 | 20250331000222 | 3 |
| 처브라이프생명보험 | 00203102 | 20250407003402 | 4 |

**Changes:**
- `src/ifrs17/universe.py`: new `AUDIT_REPORT_ANNUAL` frozenset (5 full K-ICS names) + `is_audit_report_annual()`. `list_filings` already accepted `pblntf_ty` so no client change was needed.
- `scripts/ifrs17_ingest_audit_annual.py` (new): resolves corp by exact name, picks latest standalone 감사보고서 (excludes 연결), fetch → extract → `extract_csm_tables`. Writes `data/dart/extracted/<canonical>_<rcept>_csm.json` (mirrors `ifrs17_batch_all` shape) + `_audit_annual_summary.json`. Run: **5/5 ok**.

**Notes / gotchas found:**
- NON_LISTED_SKIP held *short* names (라이나생명) while K-ICS 원수사명 are *full* (라이나생명보험), so the exact-match exclusion never actually gated these 4 — they just fell out as `no_annual_filing`. Left NON_LISTED_SKIP untouched (surgical); the new set is what F11 consults.
- **AIA (에이아이에이생명보험) is NOT in kics_disclosure.json** (no public K-ICS row) — carried in universe only; needs special-casing anywhere keyed on K-ICS names.

**VIZ HALF PENDING (checkpoint):** only A2 (amort schedule) extracted. Full dashboard parity needs A1 measurement (for waterfall/bubble), wiring into IFRS17.html selector/panels + index bubble + waterfall, the 23→28 / 생보 13→18 count copy, annual-only handling in Panel 6 (CSM 시계열 has no 13Q series for these), and AIA's non-K-ICS name.

## 2026-05-28 -- IFRS17 yearly CSM amort (F6) + KPI/BS panel pruning

**F6 — yearly CSM amort schedule (panel 2):**
- `viz_build_ifrs17_panels.py`: `extract_amort_schedule` now emits `yearly` (y1..y10 + y10plus + total) and `granularity` alongside the existing 4-bucket `buckets` (kept — `viz_build_ifrs17_kpis.py` + bubble still read buckets). New helpers `_year_bucket_cell` / `_year_bucket_indices` / `_yearly_from_aligned` / `_extract_transposed_yearly`. `granularity='yearly'` only when >=7 of y1..y10 present, so coarse-range tables (1년 이하/1~3년/...) stay `coarse`.
- Split: **16 yearly / 6 coarse / 2 no-data** (of 24); 22/24 ok unchanged.
- `IFRS17.html` panel 2: yearly bar chart, **desktop 10y / mobile 5y** (`matchMedia(max-width:640px)`); coarse companies fall back to the 4-bucket view; re-render on breakpoint change.
- Verified via `Chart.getChart`: DB생명 desktop=10 bars [268,197,…,32], mobile-load=5 bars; 삼성생명 (coarse)=4-bucket fallback. No console errors.

**Panel pruning (user review: derived proxies are non-official; raw > proxy for B2B; BS duplicates DART):**
- Removed panel "5) Downstream KPI 카드" (4 proxy KPIs) + "6) BS 스냅샷 표" from `IFRS17.html` (template + renderCompany blocks + PATHS/payload/ix/boot wiring + `.kpi-*` CSS + now-orphan `renderMatrixTable`). Generators kept (`downstream_kpis.json` still feeds the bubble's closing CSM). Definitions preserved in **`docs/archived_metrics.md`**.
- Panels renumbered 1–6 (wf / amort / pl / nb / sens / hist); intro "7패널" copy fixed.

**Roadmap:** `docs/roadmap.md` §1A-2 added — 재보험 영업 관점 6 우선 추가지표 (요구자본 위험액 세부분해, RA 규모·신뢰수준, P&L 보험/투자 분해, 출재율, 유지율, 운용자산이익률) + 🟡 후순위/제거 목록.

## 2026-05-28 -- index treemap text cleanup + mobile list sort

User feedback: desktop treemap company labels overlapped/clipped in small tiles; 지급여력기준금액 text is redundant (tile size already encodes it).
- Dropped the "기준 XXX" meta line from every cell (removed `.meta` CSS + JS).
- Size-aware labels: name shown only if cell ≥46×60px, ratio only if ≥26×44px; tiny cells show color only (no clipped text). `.cell` now `justify-content:flex-start;gap:3px` (clusters name+ratio top-left).
- Mobile list `renderList`: sort changed from ratio desc → **지급여력기준금액(required) desc**, so big insurers (삼성생명…) top, matching the treemap; bar/color still encode ratio. (User: 라이나 343% sitting on top felt off.)
- Verified via Preview: desktop labels clean & non-overlapping; mobile 삼성생명 top / 라이나 9th; zero console errors.

## 2026-05-28 -- Mobile responsive M2 (treemap -> list on phones)

The treemap can't fit 30+ insurers legibly on a 375px screen (small tiles clipped). Per research, the fix is a *different* presentation on mobile, not shrinking. index.html now swaps the treemap for a vertical list below 640px.

- New `#map-list` container + `.li-*` styles (name + colored magnitude bar + ratio%).
- New `renderList(sector)` JS: mirrors `render()` inputs — same `GROUPED` data, `colorForRatio()` scale, ratio toggle (kics/basicCapital), and click→`K-ICS.html?company=...`. Rows grouped by 생명보험/손해보험, sorted by ratio desc, bar width = ratio/maxRatio.
- Called at the end of `render()`, so every redraw (resize / sector change / toggle) updates both views; CSS @media decides which is visible.
- `@media (max-width:640px)`: `#map{display:none}` + `.map-list{display:block}` (replaced M1's map height tweak).

**Verified via Claude Preview:** mobile 375px shows clean sorted list (라이나 343% … 한화 157%), all insurers legible; desktop 1280px treemap unchanged; zero console errors. M3 (chart fine-tuning, e.g. donuts stacked) still optional.

## 2026-05-28 -- Mobile responsive M1 (shared foundation)

User asked to make the site look good on phones (index treemap "와장창 찌그러짐"). Audit found **zero `@media` queries** across all 4 pages — viewport tag present but no responsive breakpoints, so desktop layout was forced onto phones.

**M1 (this round):** added identical `@media (max-width:640px)` block to index/K-ICS/IFRS17/공시보고서.html:
- header padding↓, brand subtitle (`.hint`) hidden, container padding 16→10px
- `.tabs` horizontal-scroll (nowrap + overflow-x:auto) so tabs never wrap/overflow
- `.panel` padding↓, `.panel h2` 20→17px, `.select` smaller
- chart containers height↓ (chart-container 500→360, forward-chart 420→340, chart-sm 380→300); donut-wrap 240→200
- tables: `.table-container` overflow-x:auto, font 12px, th/td padding↓
- index map: height 76vh→58vh, min-height 560→420; bubble 360
- All scoped under ≤640px → desktop mathematically unaffected.

**Verified via Claude Preview** (python http.server :8765): mobile 375px — tabs fit one row, big insurer tiles legible; desktop 1280px — unchanged. Data loads fine over http (12,795 rows, no console errors).

**Confirmed M2 still needed:** small-insurer treemap tiles still squish on 375px (text clipped). Real fix = switch treemap→vertical list/bar below ~700px (deferred, user's choice).

## 2026-05-28 -- HTML single-source refactor (P1 + P4)

Frontend-fundamentals audit (per user's "비개발자 바이브코더" video). Diagnosed 5 정합성 issues; fixed P1 (HTML duplication) + P4 (dead dependency) this round.

**Root cause found:** `K-ICS.html` existed in both root and `templates/` and had **drifted** — only line 171 (`window.FORWARD_DATA` inline blob) differed. `forward_capital_simulation.py` wrote only to `templates/K-ICS.html` (mtime 3h newer), so the deployed root copy served **stale forward-capital numbers** (pre-face-value-fix). index/IFRS17/공시보고서 copies were still identical.

**P1 — single source = root:**
- `cp templates/K-ICS.html → K-ICS.html` (root now carries the fresh 액면가 data — fixes the stale deploy).
- `git rm templates/{index,K-ICS,IFRS17,공시보고서}.html` (4 HTML mirrors removed). templates/ now holds only data JSONs.
- `forward_capital_simulation.py`: `_sync_forward_data_into_kics_html` path `templates/K-ICS.html` → root `K-ICS.html` + docstring/WARN text. py_compile OK.
- Local preview now: `python -m http.server 8000` from repo root (was `-d templates`).

**P4 — dead dependency:** index.html dropped unused `xlsx.full.min.js` CDN (~900KB, never called; only the `<script>` tag existed, zero `XLSX.` usage). 817→816 lines.

**Deferred (noted in TODO Meta):** data-JSON duplication (templates/{kics_disclosure,tier1/tier2_utilization_latest,forward_capital_latest}.json still written by recalc_*/crawl_assoc_nb_premium/extract_ir_wolnap_benchmarks) = future P2. Remaining HTML structure todos: P3 shared CSS/nav → assets/common.css; P5 K-ICS inline data → external JSON+fetch.

## 2026-05-25 -- IFRS17 historical 13Q ingest + CSM 시계열 panel (push #2)

User asked to expand IFRS17 from FY2024 annual only to all quarters 2023.1Q ~ 2026.1Q. Built 3-stage pipeline + new IFRS17.html panel + deployed.

**Stage 1 — Historical fetch (`scripts/ifrs17_batch_historical.py`):**
- Period targets: 13Q (사업 4 + 반기 3 + 분기 6). pblntf_detail_ty {A001/A002/A003} + report_keyword filter, skip 기재정정.
- Cache by canonical/period dir. Reuse `resolve_corp` + `OpenDARTClient`.
- 442 (insurer, period) targets attempted: 226 ok (CSM extracted) + 143 no_filing (비상장 분기 미공시 정상) + 68 no_csm_table_found + 5 errors.
- raw zip cached under `data/dart/raw_history/<canonical>/<period>/`. extracted_history per-period `_csm.json` (raw csm_extractor output).

**Stage 2 — Promote to measurement (`scripts/ifrs17_promote_history_to_measurement.py`):**
- Runs `src.ifrs17.measurement_extractor.extract_measurement_tables` per (canonical, period) XML dir.
- 294 targets → 293 ok (single 1 with no_measurement_tables). Cache when ≥64 bytes.
- Output `_measurement.json` matches the picker schema in `viz_build_csm_waterfall.py` (block_type/slice_label/mvp_candidate).

**Stage 3 — Historical waterfall builder (`scripts/viz_build_csm_waterfall_history.py`):**
- Reuses `pick_main_block` + `extract_stages` + `detect_unit_scale` from the existing FY-only viz builder.
- Aggregates per-(insurer, period) snapshots into time-series payload.
- Coverage jumped 20 → **257 ok + 2 partial** (out of 299 reachable) after measurement promote step. 사업보고서(FY): near 23/23. 2025.2Q~2026.1Q has 11-13 no_csm_block each (분기보고서 often text-only).
- Output: `data/dart/viz/csm_waterfall_history.json` (319KB, 23 companies × 13 periods).

**Panel 8 — `templates/IFRS17.html`:**
- New section "8) CSM 시계열 (2023.1Q ~ 2026.1Q)". Chart.js dual-axis line.
- Selected company: 기말 CSM (좌 y, solid teal-blue) + 신계약 CSM (우 y, dashed pink). 22 background lines (회색 spaghetti) for cross-comparison.
- Tooltip + legend filter `_bg: true` datasets so only selected-co lines are interactive.
- nulls for `no_csm_block` periods (spanGaps: false) — visible as gaps.
- PATHS.hist added; payload/ix/destroyCharts/boot all extended.

**Known data-quality follow-ups:**
- 한화 2023.4Q opening ~9.8조 vs Q3 closing 13.7조 → picker selected a different sub-block. Acceptable for v1 viz; mark in changelog.
- 분기보고서 parser: ~34 cases where text mentions 신계약 CSM but rollforward not in any table. Future: pattern extend.

**Push #2:** commit e846e5a (6 files, 9271 insertions). https://solvencyk.github.io/insurequant/IFRS17.html deployed. data file 200 OK at 319KB.

---

## 2026-05-25 -- Bond tier `(신종)` fix + Kyobo/Samsung MD reparse + forward sim refresh

**Bond normalize (`scripts/normalize_bond_schedule.py`):**
- `_classify_tier` now maps FSC `(신종)`, `신종자본증권`, `하이브리드` → `tier1_hybrid` (was only literal `신종자본`).
- Re-normalize `20260525T061945Z`: tier1_hybrid **63** (was 48). KR0032 bond T1 outstanding **4500** = BS 신종 4500; KR0104 T1 **5000** ≈ BS 4999.
- Registry aliases: KR0032/KR0072/KR0104 주식회사 variants (ingest unchanged this pass — data already present).

**Forward sim v3 (`20260525T061947Z`):** confidence high **5** (+1). KR0032: `fsc_missing_t1` cleared, T1 gap 0%; still **low** on T2 face vs BS (over_deduct). KR0104: **high**. KR0072: **`fsc_missing_t1` remains** — FSC has only **called** tier1 (700억); BS still shows 2403억 outstanding 신종 (not in FSC outstanding cohort).

**Weak capital (document only, no “fix”):** KR0003 Lotte basic_cap **-3875**억 / basic ratio **-23.7%**; KR0072 KDB basic_cap **-3311**억. User-confirmed real stress, not parser error.

**MD reparse (FY2025_Q4, KR0073 + KR0069):** `DEFAULT_RATIO_KEYWORDS` + IFRS17 terms; `--keyword-window 3 --max-hit-pages 24`. Both ok conf=0.87 (~16 min). `가정민감도` sections now in MD. Sensitivity batch: KR0073 **4 tables**, KR0069 **3 tables**; FY2025_Q4 cohort **13/23** insurers, **30** tables total.

---

## 2026-05-25 -- IFRS17 B5 K-ICS sensitivity: appendix headings + multi-period batch (parser)

Moved to [`docs/changelog_parser.md`](changelog_parser.md) "2026-05-25 — IFRS17 B5 K-ICS sensitivity".

---

_(Older 2026-05-25 entries condensed into the Historical archive below; see git log for commit-level history.)_

---
## Historical archive (compressed)

Older entries condensed to one-liners (commit-level detail now in git log after first push on 2026-05-25).

### 2026-05-25 K-ICS / IFRS17 mid-session work (compressed)
- NB CSM ratio prototype: artifact `_read()` UTF-8→cp949 fallback (KB fix), Samsung Life multiline 금융 layout, ECharts axis union; `data/ir/nb_csm_ratio.embed.js`
- IFRS17 B3 row tagging: `src/ifrs17/row_normalizer.py` + `row_aliases.yaml`; 5 source files, 2956 rows scanned, 930 canonical hits
- IFRS17 B5 K-ICS sensitivity ingest v1: `kics_sensitivity_extractor.py` + `ifrs17_batch_kics_sensitivity.py`; FY2025_Q4 10/23 insurers, 19 tables
- CSM waterfall stage patterns: extended STAGE_PATTERNS; **23/23 ok**, 0 no_csm at that point
- Forward sim v2: confidence per-row, `capacity_exhausted` cap, auto-sync `window.FORWARD_DATA` inline. Run 20260525T053725Z
- Parallel multi-progress: K-ICS inline-data fix (file://) + FSC alias-loop fix (+5사: KR0010/0011/0032/0072/1098) + Phase 5 v2 cross-ref + Meritz xlsx (K-ICS 240.74%, CSM 112.9조, NB mult 12.61x, Group RoE 25.37%)
- IFRS17 CSM Waterfall picker: 5 no_csm 손보사 → 0 (MVP filter off, ceded penalty, header-in-rows hoist). 23/23 coverage
- K-ICS.html Phase 4: 자본성증권 도넛 + Forward Outlook 라인 (dual-axis, 130%/50% 기준선)
- Unit-hint mismatch auto-detect: 23 insurer-quarter latent bugs (3 ×100 + 20 ÷100), 56 post values corrected. Rule 8_post pre/post bug fixed → RED=2 (KR0010 OCR only)
- Validation rules 9 + 10 added: item2 post≥pre, item14 pre≥post (transitional consistency)
- KICS-FORWARD-CAPITAL Phase 3 v1: yearly × 5y, 19사 cohort. 롯데 2030 94.67%, 한화 158→134%, 교보 166→139%
- Bond calendar v3: 5y Call rule for ALL bonds (no name gate), 3-status outstanding/called/matured. 19.60조 outstanding. 한화 신종1 (2017→2022) called confirmed via thebell
- FSC schedule API per-insurer full pull: 1720 rows / 19 insurers (was 0)
- K-ICS gate RED=0 ex OCR (report 20260524T180329Z, 12795 rows, 25 tests passed)

### 2026-05-25 K-ICS RED reduction (cumulative)
- Rule 2 fixes (KR1098/KR0051/KR1010/KR0095): KakaoPay/MetLife reversed capital labels, item4 reconcile, item10 baseline; `_canonicalize_table_label`, MetLife alias, `labels_compatible` guard
- 8_life item35 parser fix (KR0009/KR0095/KR1098/KR0051/KR0049): multi-line unit hint, life-only 총계, default 백만원 for life catastrophe tables
- Shinhan Life (KR0094) 2024.4Q rule 6 fix: drop bare `분산효과` alias; only top-level item16 labels
- Rule 5 missing item22 (KR1010/KR1098/KR0051): recalc infers item22=0; OCR-spaced label match; rule5 RED 19→0
- Samsung Life (KR0069) 2023.1Q/3Q parse: bullet section start patterns; KR0069 0 RED all 12 quarters
- DB손해 (KR0011) 8_life: keep first 위험액 block (sub-item overwrite fix); 8_life RED 4 (was 33)
- Rule 3 always SKIP (item1 authority is rule 1); 384 buckets
- FSC schedule API 15059611 [승인] confirmed; smoke all 3 APIs resultCode 00
- KICS-VALIDATE harness re-runs across the day: RED 99→77→48→10→2 (KR0010 OCR only)

### 2026-05-25 IR + reports
- User-facing Tier1/Tier2 utilization report 2025.4Q (Korean prose, parent relay)
- Full RED export 99 cases: `red_all_cases_latest.md`/.json + `scripts/export_red_all_cases.py`

### 2026-05-25 Tier-2 / FSC bond
- Tier-2 utilization numerator fix (KIRI PDF reconcile, no double-subtract): in-range 9→34, outliers 29→4. Outlier report `output/tier2_utilization/outlier_report_20254Q.md`
- FSC bond ingest client `src/bonds/` + `scripts/ingest_fsc_bonds.py` (MISC-BOND-INGEST)
- 8_life dynamic tolerance applied (RED 177→99). Cat (a)+(b)+(d) `max(2.0, 5% × expected)`

### 2026-05-24 KICS parser / RED progression
- Session handoff Cursor → Claude
- K-ICS RED per-rule samples @177
- KR0097 Hana Life parse fix (RED 18→2)
- K-ICS missing-data reparse + item27/28 recalc fix (RED 311→217)
- Tier-2 recognition limit utilization FY2025 Q4 v1 (later refined)
- K-ICS validation RED fix pass 2 (user ground truth, RED 419→311)
- KICS-REPARSE-Q4 FY2025_Q4 refresh: parse 30/38 ok, fill_period upd=30
- K-ICS RED troubleshooting (user-verified cases)
- K-ICS JSON validation rules doc `docs/kics-json-validation-rules.md` + pipeline gate
- K-ICS validation re-run (R7 matrix fix)
- KICS-VALIDATE JSON rules harness (rules 1-8) initial
- K-ICS full reparse, validate, JSON swap (all periods)
- K-ICS parser: split-table continuation + row scope (KR0005 FY2025_Q4 golden test)

### 2026-05-24 IFRS17 dashboard + HTML viz
- IFRS17 CSM waterfall panel fix
- IFRS17 7-panel dashboard (Task B subagent + main)
- index.html blank treemap fetch + layout fix
- `scripts/viz_build_ifrs17_panels.py` rewritten (ASCII source, UTF-8 no BOM)
- index.html C-1/C-2 (no transition toggle per user)
- Item 28 basic-capital ratio post-transition (K-ICS treemap)
- K-ICS.html 보조지표(29-35) 행 + 경과조치 토글
- CSM Movement Waterfall HTML prototype v1 (IR domain subagent)
- 신선한 분석 시각화 10가지 제안 (IR domain subagent)
- NB CSM Ratio HTML prototype (line chart)
- IR 공시 visual aid 카탈로그 (손보 4 + 생보 2 = 6사) `docs/ir_visual_aids_research.md`

### 2026-05-24 K-ICS sub-items + historical
- K-ICS sub-items 16사 ZERO match 진단 + 매칭 룰 v2 (+23 rows)
- IFRS17 Open Q6-Q9 user decisions recorded
- K-ICS reparse honest status + Meritz item29 fix
- IFRS17 MVP tiers A3/A4/B1/B5 (skim extractors + 23-co batch)
- A1 gap 3사 (KB손해/코리안리/한화손해) MVP 슬라이스 fix
- K-ICS 전 분기 historical re-parse (FY2023_Q1 검증 + 배치)
- A1 23사 batch + TODO.md / CLAUDE handoff
- IFRS17 Open Q1-Q5 확정 + A1 측정요소 롤포워드 PoC
- IFRS17 CSM 추출기 강화 + 37사 일괄 자동 추출 (23/37 ok)
- K-ICS 경과조치 적용 후 값(`값_적용후`) + KR0076 보조지표 fix
- FSC data.go.kr bond APIs for Call schedule (research)
- Seibro call-schedule crawl research (no implementation)
- IFRS17 sensitivity heatmap table load fix

### 2026-05-23 Initial setup
- IFRS17 키 지표·스크래핑 우선순위 확정 (`docs/claude-agent-ifrs17.md`)
- 생명장기손해보험위험액 하위 6+1 보조지표 → kics_disclosure.json
- IFRS17 도메인 부트스트랩 (CSM 추출 PoC + 회사명 검색 흐름)

### 2026-04-25 to 04-28 Pipeline foundation
- 코드 통폐합 + Docling 파이프라인 도입 (2026-04-25)
- 디렉토리 quarter-first 마이그레이션 (2026-04-25)
- NONLIFE/LIFE 협회 단위 다운로더 (2026-04-26)
- PDF 검증/ACL 정상화 모듈 (2026-04-26)
- FY2025_Q4 하네스 일괄 실행 (parse → data → perf, pdf) (2026-04-27)
- FY2025_Q4 PDF → Markdown → kics_data.json 플랜 완료 (2026-04-28)
- FY2025_Q4 → kics_disclosure.json 직접 채우기 (749 rows) (2026-04-28)
- 과거 분기 PDF 배치 검증 + 누락 비율(27/28) 자동 산출 (2026-04-28)
