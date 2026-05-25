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

## 2026-05-25 -- NB CSM ratio prototype polish (misc IR)

- `scripts/viz_build_nb_csm_ratio.py`: artifact `_read()` tries UTF-8 then cp949 (fixes KB `kbfg_2025_4q.txt`). Samsung Life financial-ratio extraction handles multiline "금융" layout. Outputs `data/ir/nb_csm_ratio.embed.js` (and `templates/data/ir/` copies) assigning `window.NB_CSM_RATIO_DATA` so `prototype_nb_csm_ratio.html` works under `file://`. `_meta` adds `chart_axes`, `coverage` counters (`insurers_total=6`, `non_life_with_quarterly_lines=2/4`, `partial_disclosure_rows=5`, chart line-series counts `4+6`), `partial_disclosure` table rows sourced from extracts. Hanwha Life points use FY24.1Q/FY25.1Q for shared Samsung axis; retains `presentation.deck_period_labels`.
- `prototype_nb_csm_ratio.html`: ECharts wired from embedded JSON (axis union + aligned nulls); coverage blurb + partial table rendered from payload.

---

## 2026-05-25 -- IFRS17 B3 (IFRS-B3-UNIFY): liability row tagging

- `src/ifrs17/row_normalizer.py`: load `data/ifrs17/normalization/row_aliases.yaml`; substring match to `canonical_key` (longest alias wins; YAML order tiebreak).
- Batch: `scripts/ifrs17_normalize_liability.py` writes `data/ifrs17/normalized/*_liability_normalized.json` (wrapper: meta + `tables[].rows[].{cells, canonical_key}`).
- Latest PoC run (**5** source files): **2956** rows scanned, **930** canonical hits; source `삼성화재해상보험*_liability.json` was empty `[]`.

---

## 2026-05-25 -- IFRS17 B5 K-ICS sensitivity ingest + normalization manifest

- New `src/ifrs17/kics_sensitivity_extractor.py`: parse `md_inbox/FY*Q*/*.md` blocks under assumption-sensitivity headings (가정민감도), drop solvency `6-8` risk-sensitivity; output dicts align with `sensitivity_extractor.to_jsonable()`.
- Batch: `scripts/ifrs17_batch_kics_sensitivity.py` (default `FY2025_Q4`). Writes `data/ifrs17/extracted/KR*_FY2025_Q4_kics_sensitivity.json` and `data/ifrs17/crawl_manifest.json` (per-insurer flags for measurement/csm/dart sensitivity/liability/kics MD).
- Helpers: `ifrs17_measurement_ok_insurers()` uses `_batch_measurement_summary.json` as the 23-co list; code map from `kics_disclosure.json`.
- B3 starter: `data/ifrs17/normalization/row_aliases.yaml` (canonical liability row aliases).
- FY2025_Q4 run: **10** insurers with one or more extracted tables (**19** tables); **13** empty MDs (missing 가정민감도 section or no IFRS LIC/CSM grid in parse window).

---
## 2026-05-25 -- IFRS17 CSM waterfall viz: stage patterns push 23/23 ok

- `scripts/viz_build_csm_waterfall.py`: extended `STAGE_PATTERNS` (new business: e.g. `신계약 인식`, `최초 인식한 계약`; interest: `이자비용`, `당기손익 인식분`; assumption: `보험계약마진금액을 조정…`, `가정 변경`, `예실차`; amortization: `보험계약마진 상각`). Docstring corrected to `_measurement.json`.
- Outputs: `data/ifrs17/viz/csm_waterfall.json`; synced `templates/data/ifrs17/viz/csm_waterfall.json` for dashboard fetch.
- Latest run counts: ok **23**, partial **0**, no_csm **0**.

---

## 2026-05-25 -- Forward capital simulation v2 (confidence, ratio floor, HTML sync)

- `scripts/forward_capital_simulation.py`: `compute_confidence()` attached to every cohort row as `confidence`; manifest `simulation_version: v2`, artifact `forward_simulation_v2.json`, `confidence_distribution` histogram; fixed `no_data` overall scoring (was mis-labeled `low` when rank 0).
- Negative interpolated capital ⇒ displayed `ratio_pct` / `basic_ratio_pct` = 0% with `capacity_exhausted` / `basic_capacity_exhausted` (e.g. KR1098 2029–2030).
- Each run writes `templates/forward_capital_latest.json` and regex-replaces `window.FORWARD_DATA` in `templates/K-ICS.html` (inline update, no separate helper script on Windows).
- `templates/K-ICS.html`: forward panel adds confidence badge + `title` tooltip; subtitle bullet for methodology.
- Latest run: `output/kics_forward_capital/20260525T053725Z/`; bond cohort **24** insurers.

---

## 2026-05-25 -- Parallel multi-progress: K-ICS inline-data fix + FSC alias loop + Phase 5 v2 + Meritz xlsx

User reported K-ICS.html bottom panels showing no data locally (file:// fetch blocked in Chrome). Inlined 3 JSONs as `window.{TIER1,TIER2,FORWARD}_DATA` globals; kept fetch only for 3.7MB kics_disclosure.json. Then ran parallel sub-agents (IFRS17 no_csm picker + Meritz xlsx) while progressing K-ICS Phase 5 and FSC alias-loop fix in main session.

**K-ICS.html inline fix** (`templates/K-ICS.html`):
- Replaced `Promise.all([fetch(...), fetch(tier1), fetch(tier2), fetch(forward)])` with `window.TIER1_DATA / TIER2_DATA / FORWARD_DATA` inline before main `<script>`. Combined inline size ~97KB (vs 3.7MB disclosure JSON via fetch).
- centerPlugin: switched from `beforeDraw` to `afterDraw` + `chartArea` null-check (no first-paint race).
- placeholder text restoration on company-switch (was sticky `데이터 없음` after first miss).

**FSC alias-loop fix** (`scripts/ingest_fsc_bonds.py` L97-115):
- Was: `name = ref.search_names[0]` — only the primary alias tried per insurer. KR0008 alias `["삼성화재해상보험", "삼성화재"]` → only the first failed.
- Now: loop over ALL aliases per ref; dedupe at end (existing `_dedupe_rows` covers).
- Re-pull data: 1091 issuance / 2868 schedule rows (was 170 / 1720). **+5 insurers covered**: KR0010 KB, KR0011 DB, KR0032 NH농협손보, KR0072 KDB생명, KR1098 카카오페이. 24/39 now.
- Still missing 15 (likely no FSC entry): 외국계 7 + 디지털·신생 4 + 정부·특수 2 + outlier (KR0008 삼성화재, KR0069 삼성생명 — surprising; needs further alias e.g. "삼성생명보험주식회사").

**Bond normalize v3 re-run** → `data/bonds/normalized/20260525T050759Z/`: 103 outstanding + 80 called + 141 matured (was 90/53/28). tier_breakdown: 48 T1 + 276 T2.

**Forward sim re-run** → `output/kics_forward_capital/20260525T050808Z/forward_simulation_v1.json` 24사 × 5y. **New findings**: KR0032 NH농협손보 baseline 130.97% → 2030 **84.21%** (100% 하회 진입), KR0072 KDB생명 baseline **70.99%** (이미 미만). KR1098 카카오페이 2030 -704% (small-baseline outlier, cap 필요).

**Phase 5 cross-ref v2** (`output/kics_forward_capital/phase5_crossref_v2.md`):
- K-ICS MDs don't carry bond-level schedules → BS proxy cross-check.
- T1: 5y Call 가정 합리적. 5 alert (KR0011 +51% BS 한도 차감, KR0032/72/0104 -100% FSC 신종 누락, KR0068 -45%).
- T2: BS=시가평가 후 인정금액 vs face → ±50% 노이즈 정상. 메리츠/한화손해 face >> BS = 실제 call 완료. KR0010 KB face 8,860 vs BS 71,809 = FSC 부분 누락.

**Sub-agent A: IFRS17 no_csm picker fix** (done — see prior entry below).

**Sub-agent B: MISC-IR-MERITZ xlsx ingest** (done):
- Source: `https://m.meritzgroup.com/mo/ko/ir/ir1.do` AJAX `POST /web/ir1_1_search.do bd_div_cd=IR011` → JSON manifest. Plain HTTP, no JS rendering.
- Downloaded `MFG_202603(k).xlsx` (1Q26 quarterly, 885KB).
- Output: `data/ir/meritz/{factsheet_202603.xlsx, extracted_202603.json, extract_meritz_factsheet.py, README.md}`.
- KPIs (Meritz Hwajae 1Q26 standalone): K-ICS **240.74%** (예비), CSM closing 112,917억, NB CSM 4,402억 (mult **12.61x**), 보험손익 3,346억 / 투자손익 1,506억 / 당기순이익 **4,661억**. 손해율 일반 69.9% / 자동차 82.7% / 장기보험 94.3%.
- KPIs (Group consolidated): RoE **25.37%**, BPS 64,348원, EPS 3,926원, 당기순이익 6,802억.
- Gaps: 단독 RoE (그룹만 공개), 그룹 K-ICS (제도상 solo-entity).

---

## 2026-05-25 -- IFRS17 CSM Waterfall picker: 5 no_csm fixed → 23/23 coverage

- Trigger: TODO MISC-IR-PROTOTYPE followup "5 no_csm picker fix". CSM Waterfall viz had 5 손보사 in no_csm state: NH농협손해, 롯데손해, 메리츠화재, 삼성화재, 흥국화재.
- Root cause (3 overlapping issues, single picker fix):
  1. **Source-file over-filter**: `viz_build_csm_waterfall.py` was reading `*_measurement_mvp.json` (curated by `measurement_extractor.mvp_candidate`). For these 5 손보사 the MVP filter retained only the §14(3) 잔여보장/발생사고 liability rollforward, dropping the §14(4) 측정요소별 변동내역 (the actual A1 CSM-3-col rollforward). The full `*_measurement.json` always had the correct block.
  2. **Ceded vs direct ambiguity**: with the full file enabled, the picker started selecting 출재 (held reinsurance) blocks for some companies whose 원수 caption shares the same section header (e.g. AB생명 was *already* mis-picking ceded silently before).
  3. **Header-in-rows**: 흥국화재 §(5) ships without THEAD — header cells live as the first 2 rows under `rows`, so `find_csm_leaf_cols` returned [] and the block was rejected.
- Fix in `scripts/viz_build_csm_waterfall.py` (surgical, picker-only):
  - Switched `main()` glob from `*_measurement_mvp.json` to `*_measurement.json` (+ stem-strip in `build_for_file`).
  - Added `normalize_block_header(blk)` — hoists unit annotation + up to 3 leading text-only rows into `header` when `header == []`. Lines ~167-220 region.
  - Added `_is_ceded_block(blk)` — row-label primary (재보험계약자산/부채 vs 보험계약자산/부채), caption fallback when row labels mute. Used in `pick_main_block` as score -10 penalty.
  - No per-company hardcoded mapping (per user feedback `feedback_ifrs17_company_mapping`).
- Result (23/23 coverage now, 0 no_csm):
  - 7 ok (was 4): + 롯데손해, 메리츠화재, 삼성화재
  - 16 partial (was 14): + NH농협손해, 흥국화재 (4 stages each)
  - 0 no_csm (was 5)
  - 1 silent improvement: AB생명 was picking 재보험 block mislabeled as direct; now picks 원수 block (stages 3→2 but data is correct).
- Verified value magnitudes (조원-scale): 메리츠 opening 4.62조, 삼성화재 opening 13.30조, NH농협손해 opening 4.11조 — matches public reports.
- Outputs regenerated: `data/ifrs17/viz/csm_waterfall.json` + `templates/data/ifrs17/viz/csm_waterfall.json` synced. `downstream_kpis.json` re-built (20/23 ok).

---

## 2026-05-25 -- K-ICS.html bottom panels: 자본성증권 소진율 도넛 + Forward Outlook 라인 (Phase 4 done)

- User mockup (image): 좌측 도넛 2개 (기본자본=신종 / 보완자본=후순위) + 우측 라인 차트 (5y projection). 회사 selectable.
- Title choice: "자본비율 Forward Outlook (보수 시나리오)" — Stress 단어 회피 (자산/금리 충격 의미와 헷갈림). 가정 2개를 subtitle bullet으로 명시.
- `templates/K-ICS.html` (+340 lines):
  - 2 new `.panel` blocks 하단 추가 (existing company picker 재활용, listener 확장).
  - Donuts: Chart.js doughnut + centerText plugin. Color ramp: <70% teal, 70-100 orange, ≥100 red. >100% 시 fill cap 100% but real % 중앙 표시.
  - Forward chart: dual-axis (지급여력비율 y / 기본자본비율 y1) + annotation 130%/50% 기준선 + warning box. 윗부분 차트의 보조축 scaling 로직 그대로 재활용.
  - Bottom note: baseline (2025.4Q 적용후) + 2030 변화 (%p) + outstanding 자본성증권 잔액.
- Data files: `tier1_utilization_latest.json`, `tier2_utilization_latest.json`, `forward_capital_latest.json` copied to templates/.
- Company name matching: exact then partial includes (e.g. "미래에셋생명" ⊂ "미래에셋생명보험"). 19사 forward sim cohort 외 picker 회사는 "데이터 없음" placeholder.
- Brace/paren balance OK (216/216, 455/455, 95/95). UTF-8 no BOM verified.
- TODO: KICS-FORWARD-CAPITAL Phase 4 → done. Phase 5 (자본성증권 cross-ref) 남음.

---

## 2026-05-25 -- Unit-hint mismatch auto-detect (KR0001 2023.1Q + 22 latent cases) + rule 8_post fix

- Trigger: Rule 9 (added earlier in session) caught KR0001 2023.1Q item2 post=391.62 vs pre=36,312 (100x unit error). MD line 152 shows `(단위 : 백만원, %)` but actual values 39,162 are 억원 — wrong unit hint in source MD.
- `fill_post_transition_to_disclosure.py`: cross-check MD pre values vs JSON 값 (authoritative pre from main 4-2-1 table). If ratio ≈100 or ≈0.01 across multiple items (votes ≥ 2), apply scale_correction to all post values for that insurer-quarter.
- Re-run --all-periods: **23 insurer-quarter combos fixed** (3 cases ×100: KR0001/KR0008/KR0069 2023.1Q; 20 cases ÷100: KR0005/KR0068/KR0072/KR0087/KR0094/KR0095/KR1000/KR1098 across 2023.3Q-2025.4Q). 56 post values corrected. 'votes=4' typical → high confidence.
- `recalc_basic_capital_ratio_post.py` re-run: 8 item28 values updated (KR0001 64→69%, KR0002 batch, KR0003, KR0049, KR0068 2024.2Q 82→86%, etc.).
- `kics_json_rules.py` rule 8_post: pre-existing bug exposed by unit-fix — was using `bucket.get(14)` (pre item14) in denominator while item28_post uses item14_post. Fixed to use `bucket.get(14, post=True)`. SKIP semantics tightened to require any post-transition data.
- Validation `report_20260525T000831Z`: **RED=2** (KR0010 OCR only, ex-OCR=0). Rules 9+10 zero RED. Forward simulation re-run for KR0094/KR1000 (FY2025_Q4 affected). Net: 1 RED fix + 22 silent post-value bugs cleaned + 1 latent rule bug.

---

## 2026-05-25 -- Validation rules 9 + 10: transitional consistency (item2 post≥pre, item14 pre≥post)

- User callout: 푸본현대 KR0083 forward sim 결과를 보고 "경과조치 적용 후 가용자본이 더 크다"는 점을 의심. MD line 156 (실제 적용전 7,232) vs line 222 (parser pickup 11,118) vs line 874 (진짜 적용후 23,945) 검토.
- 결론: 푸본현대처럼 자본성증권 grandfather + TAC 효과 큰 사는 가용자본 적용전≠적용후 정상이지만, 일부 사는 parser column-pickup bug.
- User rule proposal:
  - 기본자본 (item2): 적용후 >= 적용전 (grandfather 신종자본증권 → basic capital ↑)
  - 지급여력기준금액 (item14): 적용전 >= 적용후 (risk-charge ramp → SCR ↓ under post)
  - 가용자본 (item1): equality NOT enforced (TAC + grandfather → diff legit; user 가설 corrected in-session)
- `src/solvency/validation/kics_json_rules.py`: rules 9 + 10 added after 8_life. SKIP when 값_적용후 absent or equal. tol = eff_tol (default 2.0).
- `docs/kics-json-validation-rules.md`: rule 9 + 10 sections added; SKIP policy summary updated.
- Validation `report_20260525T000103Z`: **RED=3** (was 2). +1 from rule 9: KR0001 2023.1Q item2 val=36,312 post=391.62 (100x unit error in val_적용후 column); item3/item28 same pattern. Rule 10 zero RED. GREEN +169, SKIP +598 (no transitional reported).
- 1건 단일 분기 parser fix 가능 (next cheap task 후보).

---

## 2026-05-25 -- KICS-FORWARD-CAPITAL Phase 3 v1: yearly × 5y forward sim (19사)

- User scope refinement: yearly × 5y (콜 5년 = 사실상 만기, 그 너머는 의미 없음). Simpler than quarterly originally planned.
- `scripts/forward_capital_simulation.py`:
  - Inputs: `kics_disclosure.json` (FY2025_Q4 items 1/2/14) + `data/bonds/normalized/20260524T233649Z/bonds_by_insurer.json` (outstanding only)
  - Numerator: baseline = item1 값_적용후 (or 값); year-Y = baseline − Σ(outstanding bonds with effective_call ≤ year-end). Basic capital = item2 baseline − Σ(tier1_hybrid bonds called).
  - Denominator: SCR_post = item14 값_적용후 (current effective); SCR_pre = item14 값 (post-transition 2032). Linear interp over (year - 2025) / 7.
  - Years 2026~2030 only.
- Output `output/kics_forward_capital/20260524T235230Z/forward_simulation_v1.json`: 19/19 ok. Manifest notes v1 caveat (53 'called' assumptions unverified vs MD).
- Key findings:
  - **롯데손해 (KR0003)**: 2030 비율 94.67% (100% 하회). SCR 1.63 → 2.07조 transitional + bond deductions. Basic capital baseline already negative (-0.39조 — parser check warranted, separate).
  - 한화생명 (KR0068): 158→134% 종합, 58→46% 기본 (T1 1.7조 Call)
  - 교보생명 (KR0073): 166→139% 종합, 95→77% 기본 (T1 1.57조 비중 큼)
  - 현대해상 (KR0009): 190→155% (모두 T2, 기본비율 65.9% 불변)
- Next: Phase 4 K-ICS.html chart panel; Phase 5 자본성증권 cross-ref to validate 53 'called' assumptions.

---

## 2026-05-25 -- Bond calendar v3: 5y Call rule for ALL bonds + assumed Called past 5y

- User callouts:
  - "name에 콜 없어도 잘 들여다보는게 좋을거같은데?" — 흥국생명보험 1(후)/5(사모/후) 등 keyword 없는 케이스 다수 존재. v2의 `_has_call_option` name gate가 너무 좁음.
  - "한화생명은 2017년 발행건 2022년에 상환한거 맞다는데 확실해?" + thebell 2022-04-18 기사 인용 — 5y Call이 실제 행사되는 것이 norm. v2의 `past_call_window` 중간 상태 (모호하게 live로 카운트)가 오류.
- v3 fix:
  - **Apply issue+5y rule to ALL bonds**, drop name keyword gate. FSC raw 조기상환일 still audit-only.
  - **3-status: outstanding / called / matured** (no past_call_window).
    - `called`: effective_call_date <= today AND maturity > today → bond assumed Called at 5y, removed from outstanding capital.
    - `outstanding`: effective_call_date > today → live in capital base.
    - `matured`: maturity_date < today.
  - `group_by_insurer` aggregates only `outstanding` into amount/tier totals.
- Output `data/bonds/normalized/20260524T233649Z/`: 90 outstanding / 53 called / 28 matured. **Outstanding 19.60조 across 19 insurers** (T1 5.39 + T2 14.21). v2 had 26.99조 inflated by 7.4조 of past_call_window bonds now correctly marked called.
- Spot-checks:
  - 한화생명 (KR0068): 8 total → 6 out (3.40조) + 2 called (신종1 2022 + 신종2 2024). T1 1.70 + T2 1.70. 신종1 called 확인 (thebell 인용).
  - 흥국생명 (KR0071): 11 total → 6 out + 3 called + 2 matured. **신종자본증권 1 (2017→2022 call) → `called`** ← 2022 흥국 사건의 그 채권. 결국 행사됨.
- Edge check: 0 bonds with effective_call > maturity (all maturity ≥ 5y from issue). No cap needed.
- Caveat: 53 'called' assumed. Phase 3 should cross-ref each insurer's K-ICS 자본성증권 발행현황 표 to flag exceptions (rare non-exercised cases like the 흥국 episode initial period).

---

## 2026-05-25 -- Bond calendar v2: 5y Call rule + 3-status taxonomy (superseded by v3 in same session)

- User callout: "콜옵션이라는게 말이 콜옵션이지 실제로는 안갚으면 큰일나" — step-up coupon + reputational risk make 5y Call de facto mandatory in Korean insurance capital instruments. Reference: 2024-12 Hanwha Life 후순위채 4000억 (10년 만기 5년 콜).
- v1 mistake: used FSC raw 조기상환일 fallback to contractual maturity → 30년/perpetual deduction dates, useless for forward simulation.
- v2 fix: `effective_call_date = issue_date + 5 years` for any bond with "콜" in isinCdNm. FSC raw kept in `fsc_call_dates_raw` for audit only (unreliable: 45/171 rows present and often = maturity).
- 3-status taxonomy (replaces binary outstanding/matured):
  - `outstanding`: effective_call_date (or maturity if no Call) > today → clean forward-simulation candidate
  - `past_call_window`: initial 5y Call passed but maturity still future → live in current K-ICS but ambiguous (cross-ref needed Phase 3)
  - `matured`: contractual maturity_date < today
- group_by_insurer: aggregates `bonds_live = outstanding + past_call_window` with tier split.
- Output `data/bonds/normalized/20260524T233306Z/`: 171 total / 92 outstanding / 51 past_call_window / 28 matured. **Live 26.99조 across 19 insurers** (T1 7.68 + T2 19.31).
- Hanwha spot-check (KR0068): 8 bonds all live (6 outstanding + 2 past_call_window 신종1/2), 4.4조 = T1 2.7 + T2 1.7. Matches FSS reality.
- Seibro 조기상환권 누락 짧은 노트: FSC API와 Seibro UI 동일 KSD 백엔드지만 비정형 자본성증권에서 메타데이터 흔히 누락. 결국 한국 시장 5년 콜 default가 더 신뢰성 높음.

---

## 2026-05-25 -- Bond schedule normalized into per-ISIN calendar (KICS-FORWARD-CAPITAL phase 2 — superseded by v2)

- `scripts/normalize_bond_schedule.py`: read latest `data/bonds/<stamp>/schedule_by_insurer.json`, collapse 발행/원리금지급일/조기상환일 events per ISIN into a calendar dict.
- Initial v1 output `data/bonds/normalized/20260524T232248Z/` used FSC raw Call dates; superseded by v2 (above) within same session.

---

## 2026-05-25 -- FSC schedule API: per-insurer full pull (1720 rows / 19 insurers)

- `scripts/ingest_fsc_bonds.py`: added `schedule` to `pull_for_insurers` endpoint loop (was `("issuance",)` only). bondIsurNm filter verified working (Hanwha Life returns real 신종자본증권 콜/원리금지급일 rows).
- `--full --max-pages 5`: `data/bonds/20260524T231206Z/` → issuance_by_insurer 170, **schedule_by_insurer 1720 (was 0)**, early_exercise_by_insurer 0 (timeout — covered by sample 200), 2 sample endpoints 200 each.
- Schedule insurer hits (top): KR0083 267, KR0009 239, KR0003 194, KR0005 165, KR0001 148, KR0002 134, KR0082 117, KR0104 106, KR0071 93, KR0087 63, KR0094 51, KR0097 49, KR0079 34, KR0068 37. Missing 20/39 insurers (name mismatch — crno lookup follow-up).
- No row capped at max_pages=5 × 100; all <500 per insurer.
- Unlocks KICS-FORWARD-CAPITAL data layer: per-bond Call/maturity calendar normalization next.

---

## 2026-05-25 -- K-ICS gate RED=0 (ex OCR); full reparse cycle

- Pipeline: `fill_period --all-periods --refresh` + `fill_subitems --all-periods --refresh` + `recalc_kics_derived` + validate.
- **report_20260524T180329Z**: RED=2 (KR0010 rule2 only), YELLOW=377, GREEN=2836, SKIP=625, ERROR=0. **RED=0 ex OCR** (KR0010/KR0079 excluded per user).
- Cumulative fixes this session: rule2 (reversed labels, item4 reconcile, item10 baseline), rule5 item22=0, item16 diversification scope, 8_life item35 unit/table, KR0069 2023 bullet section, KR0094 item16 sub-table alias.
- JSON: 12795 rows. Unit tests: 25 passed.

---
## Historical archive (compressed)

Older entries condensed to one-liners on 2026-05-25 to reduce per-session context cost. Detailed earlier versions are not retained (no git history yet — see TODO `git init + commit + push`). Each one-liner preserves: date, area, key outcome.

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
