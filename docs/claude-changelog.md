## 2026-05-29 -- 삼성생명·미래에셋 합계-vs-CSM 컬럼 식별 + 상품군 분리공시 합산 (FY anchor 정정)

User: "삼성생명/미래에셋 합계-vs-보험계약마진 컬럼 식별을 더 파고든 다음 커밋." 이전 세션의 `<TE>` 복구 후에도 삼성/미래 다수 분기가 no_csm_block으로 남았던 진짜 원인 두 가지를 규명·수정.

**근본 원인 1 — 상품군 분리공시(per-product split).** 삼성생명·미래에셋은 측정요소 변동표를 **상품군별 별도 표**(사망/건강/연금/저축/기타)로 쪼개 공시. 기존 picker는 그중 **한 상품(사망)** 만 집어 회사 전체로 착각 → 삼성 FY 마감 CSM이 **4.9조(사망 1개 상품, 게다가 전기값)** 로 나옴. 진짜 전체 = 3개 상품 합 **13.08조**(공개치와 일치).

**근본 원인 2 — 합계(소계) 컬럼 이중계상.** `find_csm_leaf_cols`의 압축 헤더 분기가 `[2,3,4,5]`(전환방법 3개 + **소계**)를 모두 더해 CSM을 **2배** 계상. 미래에셋 사망 0.79조가 1.57조로, 동양생명 2.54조가 5.08조로 뻥튀기돼 있었음.

**수정 (`viz_build_csm_waterfall.py`):**
- `find_product_segmented_csm_cols`: 상품 P개가 옆으로 나열된 **wide 표**(2025+ 분기 `<TE>` 표: 삼성 3×6, 미래 5×5)에서 상품별 CSM 컬럼 전부 식별, 그룹별 합계열은 per-product 합계 불변식으로 탐지·제외. → 2025+ 분기 복구.
- 압축 분기: sub2의 `소계`/`합계` 라벨 컬럼 제외로 이중계상 제거(`[2,3,4,5]`→`[2,3,4]`). → 동양·미래 단일상품 정정.
- `collect_current_product_blocks` + `extract_stages_summed`: 상품군 분리공시를 **합산**. 안전 게이트 — (a) 좁은 단일상품 블록만, (b) 동일 leaf 레이아웃 최빈군, (c) **전기** 캡션(`2) 전…`/말미 전분기) 제외, (d) ≥3개 상품, (e) 마감액이 서로 **near-uniform이면 거부**(연결/별도/기간 변형), (f) **product#1 재시작** 감지로 cycle 종료(전기=마감≈product#1 기초, 1% / 별도=기초·마감 둘다 ≈ product#1, 5%), (g) 한 블록이 나머지 합이면(=이미 total 존재) 거부.
- `build_for_file`(FY): 분리공시면 합산. `build_one_period`(history): 합산은 **FY anchor 정합 fallback**으로만(단일픽이 anchor에서 >45% 벗어나고 합산이 ≤35%일 때만) → 한화·KB·신한 등 segment 분리 회사 오합산 방지.

**결과:** FY anchor 정정 — **삼성 13.08조 / 미래 2.08조 / 동양 2.54조**(모두 공개치·인접분기와 정합). History: 삼성 **12/13**, 미래 10/13(8 ok+2 partial), 동양 8/13 복구, 전부 정상 규모(삼성 11.9→13.9조). **비대상 28사 FY·history 회귀 0건**, ok 셀 258(기준선과 동일하나 값 정정). 잔여 갭(삼성 2023.1Q, 미래 2023.1·3Q/2026.1Q, 동양 2025.2Q~)은 정직한 갭 — 동양 2025.2Q+는 컬럼식별이 아니라 **추출단계 잔액행이 0**으로 들어온 별개 이슈(F15, 재추출 대상). 다운스트림 csm_bubble/kpis 재빌드.

## 2026-05-29 -- CSM 시계열 결측 진짜 원인: `<TE>` 데이터셀 미파싱 (이전 "원본에 없음" 진단 철회)

User pushed back with a concrete counter-example: 한화생명 2025.3Q DART 공시에 '(3) 최초 인식한 계약의 효과' 보험계약마진 **2,228,273**이 분명히 있다 → "source import 문제"일 것. **User was right; my earlier "source-limited" conclusion was wrong** (I'd checked only 2025.2Q and extrapolated).

**Root cause = `<TE>` cells.** DART's 2025+ filings render table data cells as `<TE>` (table entry), not `<TD>`. `csm_extractor._iter_tables_with_context` only collected `<th>`/`<td>`, so every body row parsed **empty** (header captured, rows blank) → no_csm_block. The batch HAD fetched the right document (한화 2025.3Q rcept 20251113000814, 19MB; the user's 20251128001821 is a later 기재정정 — same `<te>` content). Fix: recognize `<te>` as a data cell (one line).

**Audit of all non-ok periods** (raw-XML signature scan): **HAS_DATA (parser missed real rollforward) 34**, NO_FILE (비상장 미공시) 5, genuinely-condensed (요약 반기) **only 1** (한화 2025.2Q). So nearly all gaps were parser failures, not missing data.

**Second bug surfaced by the recovery: `find_csm_leaf_cols`.** These tables use a **6-row multi-level header** with the leaf column labels (미래현금흐름/위험조정/보험계약마진/합계) in the *last* header row; the function only inspected rows 0-2 → returned `[]` → block still rejected. Added a fallback that scans all header rows and maps 보험계약마진 to its value-column index. After both fixes the rollforward parses (기초 CSM 13,065,788; 최초인식 보험계약마진 **2,228,273**).

**Picker hardening on the now-richer consolidated filings:**
- Exclude consolidation tables (관계기업/종속기업/요약재무정보/지분의 장부금액) — they mention 보험계약마진 but aren't the insurer's CSM rollforward (was mis-picking 미래에셋 2025.4Q 5.43조 equity table).
- History builder: reject a pick whose opening is still >40% off the prior close → emit an honest gap instead of a misleading number (한화 2025.2Q condensed, 롯데 2025.4Q tiny, 미래에셋 spurious).

**Diversified label patterns (user's 2nd counter-example).** 한화 2025.2Q ALSO had NB CSM — '해당 기간에 처음 인식한 계약의 영향에 따른 증가분(감소분)' = **1,378,511** — which I'd missed because my audit signature used '최초 인식' not '처음 인식'. The extractor's STAGE_PATTERNS already handle '처음 인식'; the real miss was the **picker** not selecting the total block among the segment sub-tables (전환일에 존재했던 계약 등) when the continuity search only scanned the top-5 candidates.

**Two more picker fixes:**
- Continuity searches **ALL** candidates (not top-5): the total often ranks below segments but its opening matches the prior close (한화 2025.2Q total 13.07조 vs segment 4.16조). Recovered 한화 2025.2Q (NB 1,378,511).
- **FY-anchor regime correction** (history builder): the pick's closing must sit within 45% of the company's FY total (`csm_waterfall.json`); if it's off, take the nearest anchor-consistent (≤35%) candidate, else emit an honest gap. Fixes systematic segment-vs-total mis-picks (교보생명 was ~5조 segment vs 11.75조 total → now ~11-13조 across all quarters). main() builds each company chronologically, threading prior-close + FY anchor.

**Result (re-promote from cached raw, no re-fetch):** ok 258 / no_csm 29 / partial 6 (was 257/34 with *wrong* "ok" values); **outlier scan = 0**; **FY 28-co waterfall 0 regressions**. Recovered with correct values: 한화 all 13Q (NB 2025.2Q 1,378,511 / 2025.3Q 2,228,273), 교보 all quarters, 삼성화재 2025.2Q/3Q, 현대해상, 케이디비, 코리안리. Recent-period coverage 2025.2Q 17/23, 2025.3Q 14/23, 2025.4Q 20/23, 2026.1Q 13/23 — all anchor-consistent. Pipeline: csm_extractor `<te>` + find_csm_leaf_cols deep-header fallback + rank_main_blocks consolidation filter + history continuity(all)/FY-anchor/reject.

**Remaining (F15):** ~24 period-cells still gap — 5 NO_FILE (비상장 미공시, genuine), plus periods where the total rollforward isn't anchor-consistent (삼성생명/미래에셋 some quarters: the leaf-col fallback picks a 합계/wrong column giving 30-37조 vs FY 4.9조; 동양생명 zeros). These need per-company column disambiguation — a deeper follow-up, not claimed fixed.

## 2026-05-29 -- Panel 5 sensitivity rowspan fix + 한화 2023.4Q dip + 2025.2Q/3Q diagnosis

User flagged (from 한화생명 Panel 5/6): the ΔCSM sensitivity table mis-aligned ("3.27% 감소" in the 위험요인 column), the 2023.4Q CSM dip, and the 2025.2Q/3Q gaps.

**Panel 5 sensitivity — rowspan + header-aware parse (`viz_build_ifrs17_panels.py`).** The risk name spans the 증가/감소 row pair via HTML rowspan, so the 감소 row has one fewer leading cell → every column shifted left (the user's exact symptom). Added `_band_sensitivity_columns` (header-aware: finds the 변동금액 보험계약마진 / 당기손익 value columns, preferring 원수; uses the LAST CSM column so 교보's 기준금액+변동금액 layout maps to 변동; strips label cells like 케이디비's 위험변수/변동; accepts 보험서비스마진 K-ICS term) + `_extract_sensitivity_band` (detects rowspan-elided continuation rows and inherits the risk). Routed only when that band header is present, so the product-line path (삼성, unchanged) and generic path are untouched. **Fixed: 한화 (사망률 증가 ΔCSM −256,319 / 손익 +80,535; 감소 +262,227 / −84,260), 교보, 케이디비 (−57,369 / −308,997), DB생명.** 삼성생명 verified unchanged. **Remaining: 흥국생명** — different layout (products-as-rows × 당기말/전기말 with 'CSM'/'손익 효과' headers); needs its own path → follow-up.

**한화 2023.4Q dip (9.24조 → 13.30조).** The FY2023 report has two near-identical "(5) 측정 요소별 변동" rollforwards: a 13.30조 total and a 9.24조 subset; `pick_main_block` chose the subset because its caption kept the 당기 marker (period_affinity 35 vs 0). Fix: exposed `rank_main_blocks` and added a **guarded continuity tiebreak** in the history builder — when the default pick's opening deviates >25% from the prior period's closing AND another top candidate opens within **5%**, prefer continuity. `main()` now builds each company's periods chronologically, threading the prior closing. The 5% guard fixes 한화 + several clearly-broken tiny values (롯데 2025.4Q 0.03→4.92조, 메리츠 2026.1Q 0.05→11.1조, 신한 14.7조, 케비 3.4조, 미래에셋) **without** touching ambiguous mid-range picks (삼성생명 stays 4.906 = consistent with the FY Panel-1 waterfall). FY waterfall **0 regressions**; outlier scan (closing < 40% of company median) now **0**.

**2025.2Q/3Q/2026.1Q gaps — confirmed source-limited (NOT a parser bug).** Verified 한화's 2025.2Q is a **요약(condensed) 반기연결재무제표**: the 21MB filing has **zero** rollforward-table signatures (`최초 인식한 계약`, `신계약효과`, `측정요소별 변동` all 0); the CSM figures appear only in narrative prose ("보험계약마진 13조"). The "141 blocks" the measurement extractor emitted are narrative/layout tables with empty rows (dedup → 1). 12/23 insurers whose 반기 reports DO carry the table already render; the other 11 (incl 한화) genuinely omit it in condensed quarterlies (2026.1Q reports defer to the audit report). → TODO **F15** (narrative/IR-supplement, or accept the gap).

## 2026-05-29 -- NB CSM multiple (Panel 4): plausibility gate + Samsung Life 사망 misparse fix

User flagged 삼성생명's 종신/사망 NB CSM multiple showing >400x (impossible; realistic max ~30-50x) and that the panel stops at FY25.1Q.

**400x = regex misparse [fixed].** `viz_build_nb_csm_ratio.extract_samsung_life` read the death row with a positional 5-number regex; the IR PDF text interleaves the death *multiples* (single digits) with absolute CSM amounts (십억원: 459/435/520/471/488) on adjacent lines, so it grabbed 520/471/488 for FY24.1-3Q. **Fix:** scan the region between the 건강 row and the (last) 사망 label, keep only `\d+\.\d+` values < cap → death now [7.6, 10.0, 7.6, 7.2, 5.1]. (`rfind("사망")` — the first 사망 is the column header 건강 사망 금융.)

**Plausibility gate [new validation rule].** `MAX_PLAUSIBLE_MULTIPLE = 60.0` + `validate_plausible(payload)` called in `build_payload` — fails the build if any chart series multiple is `<=0` or `> 60` (an absolute amount misread as a ratio). Negative-tested: catches 520x, passes 7.6x. Browser-verified on a fresh origin: Panel 4 death line ~5-10x, y-axis 0-18x, zero console errors. `validate_nb_csm_multiple` (computed-vs-IR) still 5/6 pass (한화 period-mismatch, pre-existing).

**Why Panel 4 stops at FY25.1Q [diagnosis, not staleness].** Panel 4 is **not** the computed CSM÷premium pipeline — it scrapes ratios directly from 6 IR PDF text extracts (`artifacts/ir_research/`), and Samsung Life's is hardcoded to the **FY25.1Q IR deck** (`FY24_QS` = 5 quarters). The *computed* multiple (what would extend to 2025.4Q) needs the 월납환산 초회보험료 denominator, but **`nb_premium_wolnap.json` has `kidi_ml02_row_count: 0`** — the 보험개발원(KIDI) crawl returns zero rows; only 6 single-period IR premiums exist. So the **premium (denominator) side is the unfinished half** = open **TODO F2 v3** (KIDI segment-match crawler). The CSM numerator is parsed through 2025.4Q. Extending the panel requires either F2 v3 (KIDI) or ingesting newer IR decks.

## 2026-05-29 -- CSM 시계열 (Panel 6) fixes: prior-period de-contamination + per-quarter new-business

User asked why 한화생명's CSM time series stops at 2025.1Q and flagged the new-business sawtooth. Investigation found it was **not** staleness — three separate issues:

1. **Prior-period contamination [real bug].** `pick_main_block._period_affinity` penalized `전기` but **not `전분기`/`전반기`**, so 분기/반기 reports' prior-period column was chosen. 한화 "2025.1Q" closing was literally 2024.1Q's value (13,362,336). Across 23 insurers, 13-17 quarterly points per period were prior-period dupes. **Fix:** added `전분기`/`전반기` penalty (−22) + `당분기`/`당반기` bonus (+22), guarded so a combined "당분기 및 전분기" caption stays current. Re-ran `viz_build_csm_waterfall_history.py` (reuses the picker on cached extracts — **no re-fetch**). Result: **prior-period contamination 0 across all periods**; 한화 2025.1Q now 12,994,325 (caption "1) 당분기"). FY28 current-panel waterfall verified **zero regression**.
2. **FY2025 (2025.4Q) was always present** (20/23 ok) — it just rendered as an isolated dot because 2025.2Q/3Q are null (line break). Not a data gap.
3. **2025.2Q/3Q/2026.1Q gaps** (~11/23 no_csm_block): genuine — 반기/분기보고서 often lack a parseable rollforward (2026.1Q reports defer to the audit report). **Deferred** (a parser-improvement task, user's choice).

**New-business → per-quarter increment.** New-business CSM is disclosed fiscal-YTD cumulative (Q1/H1/9M/FY) → within-year sawtooth. `viz_build_csm_waterfall_history.add_nb_increments` now emits `new_business_increment_mn_krw` (+ `_span_q`): flow since the previous available quarter in the same FY, chain persisting across an unobserved quarter (so an annual point with missing 9M reports the Q2-Q4 flow, span_q=3, rather than a reset). IFRS17.html Panel 6 plots the increment for the pink line (기말 balance/blue line unchanged — it's a stock), axis/label/caption updated, tooltip flags multi-quarter spans. Verified for 한화: new-business now ~0.7-1.1조/quarter (no sawtooth); 2025.4Q dot = 2.42조 (span 3Q, flagged). Zero console errors.

## 2026-05-29 -- F11 DONE: foreign-affiliate life insurers fully in IFRS17 dashboard

User pushed to start F11 (add 5 foreign-affiliate life insurers to IFRS17), then approved full viz integration. Result: IFRS17 cohort 23→28 (생보 13→18), all 5 rendering in the dashboard + index bubble. Browser-verified, zero console errors, zero regression to the existing 23.

**Viz integration was glob-driven — almost no HTML change.** The builders enumerate `data/ifrs17/extracted/*.json` (panels: `*_csm.json` / `*_insurance_pl_mvp.json` / `*_sensitivity_mvp.json`; waterfall: `*_measurement.json`) and IFRS17.html builds its company selector from `wf.companies`, index.html bubble from `csm_bubble.json`. So producing the standard artifacts auto-grew the selector (28 options) and the bubble (28 points). nb + hist panels stub gracefully for the 5 (no IR premium mapping; not in the 23-co 13Q history cohort).

- `scripts/ifrs17_ingest_audit_annual.py`: extended to also run measurement / insurance_pl / sensitivity extractors on the already-fetched audit-report XMLs (same artifact names the per-tier batch scripts emit). Re-run: 5/5 ok (meas 8-25, pl_mvp 1-10, sens_mvp 16-41 tables).
- Re-ran `viz_build_csm_waterfall.py` (28 co), `viz_build_ifrs17_panels.py` (pl 28/28, sens 18/28), `viz_build_csm_bubble.py` (csm 28, the 5 grey = no NB multiple).

**3 safe waterfall-builder fixes** (`viz_build_csm_waterfall.py`), each verified zero-regression against a snapshot of the 23:
1. Magnitude unit fallback now keyed on the **largest-magnitude stage**, not opening — these insurers report in **천원** and some split the 기초 row so opening matched a zero placeholder (메트/AIA/하나 scale).
2. `pick_main_block`: **direct block always outranks ceded** (new top sort key). 처브라이프's `<당기>`-tagged 재보험계약부채 block had been beating its direct 보험계약부채 block → fixed (closing 1,124억, was negative/wrong).
3. Closing label `보고기간말` added + a **guarded** net-row patch: when opening/closing resolves to ~0 (rowspan-split 자산/부채/순부채 balance, e.g. 하나생명), pull the 보험계약순부채 net row's CSM. Guard (only fires on ~0) keeps the 23 untouched. 하나 fixed: open 3,016억 / close 4,390억.

Final waterfall status for the 5: 메트라이프 / AIA / 처브라이프 / 하나생명 **ok**; 라이나생명 **partial** (its rollforward has no matched amort row; Panel 2 amort schedule is clean from csm.json).

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
- `scripts/ifrs17_ingest_audit_annual.py` (new): resolves corp by exact name, picks latest standalone 감사보고서 (excludes 연결), fetch → extract → `extract_csm_tables`. Writes `data/ifrs17/extracted/<canonical>_<rcept>_csm.json` (mirrors `ifrs17_batch_all` shape) + `_audit_annual_summary.json`. Run: **5/5 ok**.

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
- raw zip cached under `data/ifrs17/raw_history/<canonical>/<period>/`. extracted_history per-period `_csm.json` (raw csm_extractor output).

**Stage 2 — Promote to measurement (`scripts/ifrs17_promote_history_to_measurement.py`):**
- Runs `src.ifrs17.measurement_extractor.extract_measurement_tables` per (canonical, period) XML dir.
- 294 targets → 293 ok (single 1 with no_measurement_tables). Cache when ≥64 bytes.
- Output `_measurement.json` matches the picker schema in `viz_build_csm_waterfall.py` (block_type/slice_label/mvp_candidate).

**Stage 3 — Historical waterfall builder (`scripts/viz_build_csm_waterfall_history.py`):**
- Reuses `pick_main_block` + `extract_stages` + `detect_unit_scale` from the existing FY-only viz builder.
- Aggregates per-(insurer, period) snapshots into time-series payload.
- Coverage jumped 20 → **257 ok + 2 partial** (out of 299 reachable) after measurement promote step. 사업보고서(FY): near 23/23. 2025.2Q~2026.1Q has 11-13 no_csm_block each (분기보고서 often text-only).
- Output: `data/ifrs17/viz/csm_waterfall_history.json` (319KB, 23 companies × 13 periods).

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

## 2026-05-25 -- IFRS17 B5 K-ICS sensitivity: appendix headings + multi-period batch

- `src/ifrs17/kics_sensitivity_extractor.py`: section starts also recognize markdown titles that contain both ``보험위험`` and ``민감도`` (appendix wording without the contiguous ``가정민감도`` token); compact-line match for spaced ``가정``/``민감도``; bullet ``- (5)`` only when assumption-sensitivity wording matches. Default ``min_score`` lowered to **3** so IFRS LIC/CSM grids that land at score 3 after the +2 K-ICS bump are emitted (fixes e.g. 미래에셋 변형 표 헤더 cases). Solvency-only ``6-8`` blocks unchanged.
- `scripts/ifrs17_batch_kics_sensitivity.py`: `--all-periods` runs every ``md_inbox/FYyyyy_Qn`` directory; ``--manifest-period`` selects the ``crawl_manifest.json`` period (default last sorted). JSON output includes ``tables_grand_total_across_periods``.
- Latest full run (12 quarter folders on disk): **49** tables extracted across all periods; FY2025_Q4 **11** insurers with >=1 table (**23** tables) vs legacy headings + ``min_score=4`` baseline **10** / **19**. KR0073/KR0069 still empty: FY2025_Q4 MD lacks IFRS 가정 민감도 grid in the keyword parse window (upstream MD scope), not fixable by regex alone.

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
