# Insurequant TODO

Last updated: 2026-05-26 (F2 v3 segment-match scope; F4 v2 KB라이프 분류 정정; Top-3 alias만 액션, 나머지 8사 defer)

## 🚧 Follow-ups (next session — 병렬 sub-agent 대상)

| # | Task | Scope | Notes |
|---|------|-------|-------|
| ~~F1~~ | ~~index.html → IFRS17 cross-nav~~ | done | `fcdd544`. ECharts on('click') → URL param + auto-select |
| F2 v3 | **NB CSM 배수 — segment-match KIDI crawler** | **scope 재정의 2026-05-26**: 신계약CSM 분자가 상품군별로 분리 가능하면 (건강/저축 등) → 같은 segment 월납환산 초회보험료를 분모로. 분리 불가면 **보장성보험 (투자계약 제외) 초회보험료 (월납환산)** 만 사용 (손보·생보 둘 다). IR 자료 있는 6사는 산출값 vs IR값 비교 검증. | KIDI endpoint 확인 완료: `POST /insMonth/getQueryResult.do queryId=getM{XX}List`. 손보 N07 row LINE=99113 = 보장성보험 합계 (개인 + 단체). 생보는 070104 ML04List (종목별 I — 보장 분리됨) 확인 필요. ITEM_VAL 컬럼 의미 매핑은 KIDI 웹 UI 시각 cross-check 필요 (한화 메리츠 작은 N월 값 vs 큰 N월값 패턴 보고). 다음 세션 액션: (a) 070104 schema probe + 보장성 row 식별 (b) 손보 99113 row 사용 검증 (c) 생보 CSM이 segment 분리되는지 확인 — 한화/삼성 IR PDF 참조 (d) crawler 작성 (e) 6 IR-cohort 산출값 vs IR값 cross-check |
| ~~F3~~ | ~~CSM 상각 schedule 전수 조사~~ | done | `4b06492`. 19/24 → **22/24 ok**. 메리츠화재 4-bucket 정상 렌더. 헤더 패턴 (1년미만/30년이상/이하/초과 등) + transposed table + 합계 derive + reinsurance downrank. 2 source-level 한계 (서울보증 PAA, 한화손해 csm.json만) |
| F4 v2 | **Forward Outlook confidence — Cat C/D 리서치 + 외국계 분류 helper** | scope 좁힘 (cat E 정상 제외 / cat F 코드 fix 완료) | F4 v2 report: `output/kics_forward_capital/confidence_low_rootcause_v2_20260525T145147Z.md`. **Cat B drill-down 결과**: 11사 (10 아님) — KR0069 삼성생명 BS T2 66,289억 (FSC alias 최대 gap), KR0008 삼성화재 4,097억, KR1000 코리안리 4,431억 = alias 해결 시 75,000억 격차 해소. **Cat C/D 리서치 필요**: BS 자본성증권 carrying value 정의 (FV vs amortized) + Call exercise 시 차감 메커니즘. 답 나오면 over/under_deduct 의미 재정의. **외국계 분류 helper** 코드 추가 권고: `bond_coverage="no_self_issued, parent_capital"` 등 |
| ~~F5~~ | ~~No-bond insurer forward sim 추가~~ | done | `b02e24d`. 24 → 37 cohort. KR0008 삼성화재 263%→263% flat. 13 no_bond insurer 추가. F4 추가 fix (`<1.0` 임계): KR1010 교보라이프 low→high |



Session start: read TODO.md then docs/claude-changelog.md (top first).

NOTE: English only. Korean encoding is fragile across the toolchain. See CLAUDE.md "Document/TODO Encoding Rule".

## User decisions (2026-05-24)

| # | Decision |
|---|---|
| 1 | K-ICS skip cohort: KR0029 AIG, KR0150 SGI permanent skip. KR0051 / KR0074 partial-coverage by design. |
| 2 | Meritz IR source: Meritz Financial Group factsheet xlsx at https://m.meritzgroup.com/mo/ko/ir/ir1.do (replaces Meritz Hwajae standalone). AIG IR: skip low-priority |
| 3 | NB CSM ratio denominator: **월납환산 신계약보험료** (IR calls it 월납월초). IR PDF for 6 cos; **assoc crawl** (KIDI/KLIA/KNIA) for 23-co computed multiple — see IFRS17-CSM-BUBBLE |
| 4 | First HTML viz: CSM Movement Waterfall (IFRS17 A1 23-co) |
| 5 | API keys: repo root `.env` only (gitignored). OpenDART=OPENDART_API_KEY; FSC bonds=DATA_GO_KR_BOND_ISSUANCE_KEY + DATA_GO_KR_BOND_REDE_KEY. Never commit/log key values |
| 6 | Bond Call rule: issue + 5y for ALL bonds (Korean market convention; ignore "콜" keyword gate). Past 5y = assume `called` (de facto mandatory per thebell/흥국 cases) |

## IFRS17

Universe: 23 insurers (`src/ifrs17/universe.py`).

| ID | Task | Status | Notes |
|----|------|--------|-------|
| IFRS-Q | Open Q1-Q9 | done | All 9 confirmed |
| IFRS-A1 | measurement rollforward | done | 23/23 MVP |
| IFRS-A2 | CSM amort | done | 23/23 |
| IFRS-A3 | insurance P&L | done | 23/23 MVP |
| IFRS-A4 | reinsurance rollforward | done | 23/23 MVP |
| IFRS-B1 | BS snapshot | done | 23/23 MVP |
| IFRS-B5 | sensitivity DART skim | done | 23/23 MVP. PoC only per Q8 |
| IFRS-B5-KICS | B5 K-ICS primary ingest | done | FY2025_Q4 **13/23** nonempty, **30** tables. KR0073 **4** + KR0069 **3** after IFRS keyword MD reparse (2026-05-25). |
| IFRS-B3-UNIFY | B3 = section8 long-format | done | ``src/ifrs17/row_normalizer.py`` + ``scripts/ifrs17_normalize_liability.py``; PoC **5** ``*_liability.json`` → ``data/ifrs17/normalized/*_liability_normalized.json``; **2956** rows scanned, **930** ``canonical_key`` hits (**1** empty source file: 삼성화재) |
| IFRS-NORMALIZE | 23-co full normalization | in-progress | ``data/ifrs17/crawl_manifest.json`` lists artifacts per insurer |
| IFRS-P3 | half/quarter reports | eligible | MVP complete |
| IFRS17-SEN-TABLE | sensitivity heatmap panel table load | done | sensitivity_heatmap 14/23 ok |
| IFRS17-HTML-DASH | templates/IFRS17.html 7-panel dashboard | done | ECharts panel 1 + Chart.js 2-4; Samsung Life sensitivity table renders |
| IFRS-HIST | Historical 13Q ingest 2023.1Q~2026.1Q | done v1 | `scripts/ifrs17_batch_historical.py` + `_promote_history_to_measurement.py` + `viz_build_csm_waterfall_history.py`. 299 targets → 257 ok + 2 partial + 34 no_csm_block (분기보고서 text-only) + 5 errors. 사업보고서 23/23 거의 완벽. Output: `data/ifrs17/viz/csm_waterfall_history.json`. IFRS17.html Panel 8 "CSM 시계열" (dual-axis 기말+신계약, 22사 회색 배경 spaghetti) |

## index.html (market map)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| INDEX-C12 | treemap + IFRS17 quadrant | done | Post-transition default for items 27/28; IFRS17 quadrant below treemap |
| INDEX-IFRS17-BUBBLE | CSM bubble below K-ICS treemap | in-progress | size=CSM, color=NB CSM mult; `csm_bubble.json` + `viz_build_csm_bubble.py`; K-ICS treemap unchanged |

## K-ICS

| ID | Task | Status | Notes |
|----|------|--------|-------|
| KICS-SUB | sub-items 29-35 | done | Permanent skip KR0029/KR0150; image-only KR0010/KR0079 manual OCR |
| KICS-POST | values_post-transition | done | Historical reparse auto-fill |
| KICS-RATIO28 | item28 basic-capital post-transition | done | 133 rows `값_적용후` |
| KICS-HIST | historical reparse 9 periods | done | BATCH_END 2026-05-24T11:08:19Z |
| KICS-HTML-SUB | K-ICS.html sub-items + transition toggle | done | templates/K-ICS.html + JSON sync |
| KICS-TIER2-UTIL | tier2 utilization 2025.4Q | done | KIRI PDF reconcile; 34/38 in 0-100%; output/tier2_utilization/ |
| KICS-TIER1-UTIL | tier1 hybrid utilization 2025.4Q | done | SCR×15% strict 10%; 35/38 valid; output/tier1_utilization/ |
| KICS-RULES-DOC | validation rules authoritative doc | done | docs/kics-json-validation-rules.md |
| KICS-PARSER-SPLIT | parser split-table + row scope fix | done | KR0005 FY2025_Q4 golden test |
| KICS-REPARSE-Q4 | FY2025_Q4 parse refresh | done | parse 30/38 ok; JSON 10028→10454 |
| KICS-KR0069 | Samsung Life all-quarters validation | done | Parser bullet-section fix; 0 RED all 12 quarters |
| KICS-KR0097 | Hana Life parse fix | done | RED 18→2 |
| KICS-RED-FIX2 | user-verified RED pass 1 | done | RED 419→311 |
| KICS-RED-FIX3 | missing RED reparse + item27/28 | done | RED 311→217 |
| KICS-RED-SAMPLES | per-rule RED export | done | scripts/summarize_red_findings.py |
| KICS-VALIDATE | rules 1-10 harness | done (ex OCR) | **RED=2** (KR0010 OCR only). report_20260525T000831Z. Rules 9 (item2 post≥pre) + 10 (item14 pre≥post) added 2026-05-25. fill_post_transition auto-detects unit hint mismatches via JSON 값 cross-check (×100 or ÷100 correction); 23 insurer-quarter combos fixed (3 ×100 + 20 ÷100). Rule 8_post latent bug (pre14 in denominator) also fixed → uses post14 consistently |
| KICS-IMG | image-only PDF manual OCR | todo | KR0010 KB Sonhae, KR0079 Mirae Asset, KR0080. Validator tol=10 for IMAGE_OCR_COMPANIES; manual OCR still needed for rule2 large diffs |

## Misc (IR and bonds)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| MISC-IR-CATALOG | IR visual-aid catalog 6 cos | done | docs/ir_visual_aids_research.md |
| MISC-IR-NB-DENOM | NB CSM ratio denominator + validation | in-progress | Crawl/extract → compute → validate vs IR. **Waterfall:** `validate_csm_waterfall.py` **23/23 pass** (NB required + rollforward identity). **NB mult:** 5/6 IR cohort pass (한화 period mismatch FY24 vs 1Q25). Loop: `run_ifrs17_csm_reconcile_loop.py` |
| MISC-IR-PROTOTYPE | viz prototype | in-progress | CSM Waterfall **23/23 ok** + validation. **NB CSM ratio:** IR 6-co. **index.html bubble:** `viz_build_csm_bubble.py` |
| MISC-IR-MERITZ | Meritz Financial Group factsheet xlsx ingest | done | 2026-05-25 — `data/ir/meritz/` (xlsx + extracted JSON + README). 1Q26: K-ICS 240.74%, CSM 112,917억, NB CSM mult 12.61x, Net income 4,661억 (Hwajae standalone). Group RoE 25.37%. Page: plain HTTP+AJAX, no JS required |
| MISC-BOND-KEYS | FSC API keys in .env | done | DATA_GO_KR_BOND_ISSUANCE_KEY + REDE_KEY |
| MISC-BOND-INGEST | FSC bond issuance + Call schedule ingest | done | 2026-05-25 v2 alias-loop fix. Latest pull 24 insurers. **15 missing accepted**: 외국계/디지털/특수법인 + KR0008/KR0069 likely no capital-instrument issuance (user 2026-05-25) |
| MISC-BOND-NORMALIZE | Bond schedule → per-ISIN calendar | done | Latest `data/bonds/normalized/20260525T061945Z/`. tier1 **63** + tier2 261 (was 48+276). `_classify_tier` recognizes `(신종)` / 신종자본증권 / 하이브리드 — fixes KR0032/KR0104 T1 mis-tag. |
| MISC-SEIBRO | Seibro HTML fallback | todo (low) | m.seibro.or.kr smoke ok; lower priority since FSC works |

## Long-term projects

| ID | Task | Status | Notes |
|----|------|--------|-------|
| IFRS17-CSM-BUBBLE | index.html IFRS17 bubble (CSM size × NB multiple color) | in-progress | Pipeline: crawl → `validate_csm_waterfall.py` → `validate_nb_csm_multiple.py` → `viz_build_csm_bubble.py`. **Waterfall validation 23/23.** Samsung/Meritz/Samsung Life NB CSM fixed (당기 block + non-zero sub-rows). |
| IFRS17-NB-RECONCILE | NB CSM multiple validation reconcile loop | in-progress | `run_ifrs17_csm_reconcile_loop.py` orchestrates measurement re-extract → waterfall → both validators → bubble. **Remaining:** 한화생명 FY24 numerator vs IR 1Q25 denominator — align quarter or override in `nb_premium_overrides.yaml` |
| KICS-FORWARD-CAPITAL | Forward solvency simulation chart in K-ICS.html | done v3 | v3 confidence uses `subordinated_eok` not numerator residual. Post tier-fix: KR0032 T1 bond=4500=BS; KR0104 **high**; KR0072 T1 still `fsc_missing_t1` (all FSC 신종 **called**, BS 2403). KR0003/KR0071 weak capital documented (no data fix). Latest `20260525T061947Z/forward_simulation_v3.json`. |

## Meta

- Encoding rule: CLAUDE.md "Document/TODO Encoding Rule" added 2026-05-24
- .gitignore: data/ifrs17/raw/, data/ifrs17/reports/ excluded
- 2026-05-25 doc trim: changelog 124KB→11KB (latest 5 entries detailed + historical archive 1-liners). TODO.md done-task Notes compressed
- git: **not initialized** — `git init + commit + push` pending in Next priorities #5

## MVP checklist (IFRS17)

- [x] A1 A2 A3 A4 B1 B5 all 23/23 MVP (B5 K-ICS primary ingest done FY2025_Q4)

## Next priorities

1. **KICS-IMG manual OCR** (user-owned): KR0010 KB Sonhae rule2 x2 — only remaining RED
2. **IFRS-B3-UNIFY coverage**: extend `row_aliases.yaml` for higher hit rate (current PoC **930**/2956 tagged)
3. **IFRS-NORMALIZE**: extend K-ICS sensitivity to remaining empty FY2025_Q4 life insurers (Hanwha/Heungkuk/KDB etc.)
4. **IFRS17-NB-RECONCILE**: fix validation fails (period/scope/unit); extend KIDI/KLIA FY24 crawl; re-run validate until IR cohort pass
5. **git init + commit + push** (.git not yet initialized)
