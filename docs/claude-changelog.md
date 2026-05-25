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
