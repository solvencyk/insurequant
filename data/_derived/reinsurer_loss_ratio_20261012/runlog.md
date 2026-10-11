# Reinsurer loss-ratio assumptions (KR1101~KR1107, + KR1108 / KR1011 absence) — runlog 2026-10-12

Ticket `inbox/parser/20261012T0100Z__orchestrator__KR1101-KR1108_2023.4Q-2025.4Q__reinsurer_loss_ratio_assumption.md` (parser-ifrs17, loss-ratio domain). Not committed, not pushed. Shared ticket not edited.
Evidence folder: `data/_derived/reinsurer_loss_ratio_20261012/` (this file, census csv, mapping csv, HEAD key diff, cross-filing comparison, renders in `png/`).

## 0. Root cause (why the site showed 「공시 없음」)
The loss-ratio masters were built on 2026-10-08 12:58 from 37 companies. The reinsurer raw PDFs (KR1101~KR1108) were downloaded 2026-10-08 22:4x, after that build, so the extractor never saw them.
The text layer exists in every reinsurer PDF. The generic extractor `scripts/extract_loss_ratio.py` could read only part of them (KR1103/1104/1105/1107-FY2024); the other layouts need a ruled-grid reader (see 3).

## 1. Census (table ① 보험금 예실차비율 / table ② 위험보험료 대비 예상보험금), per company x annual filing
Full per-year rows: `reinsurer_table_census_20261012.csv` (89 rows; columns: present / census status / pages / text layer / evidence phrase). Summary (page numbers = PDF pages):

| company | FY2023_Q4 filing (2023.4Q) | FY2024_Q4 filing | FY2025_Q4 filing |
|---|---|---|---|
| KR1101 뮌헨 | absent (no 4-6-4 최적가정 section; keyword 0, 71/71 text pages) | ① p17 (2024, 2023) · ② p17-18 (2024 only; no 2023 block printed) | ① p20 (2025, 2024) · ② p20-22 (2025 p20-21, 2024 p21-22) |
| KR1102 스위스리아 | absent (same, 85/85 text pages) | ① p19 (2024 only) · ② p20-21 (2024; no year caption row, blocks [생명보험]/[손해보험]) | ① p22 (2025, 2024) · ② p23-26 (2025, 2024 x 생명/손해) |
| KR1103 제네럴 | absent (29/29) | ① p11 (2024, 2023) · ② p12-13 (2024, 2023) | ① p11 (2025, 2024) · ② p12-13 (2025, 2024) |
| KR1104 하노버 | absent (103/103) | ① p19 (2024, 2023) · ② p20-21 (2024, 2023) | ① p19 (2025, 2024) · ② p20-21 (2025, 2024) |
| KR1105 RGA | absent (p10 hit is a profit-commission sentence, not the table; 322/327 text pages) | ① p20 (2024, 2023) · ② p21-22 (2024, 2023) | ① p19 (2025, 2024) · ② p20-21 (2025, 2024) |
| KR1106 스코리 | absent (148/148) | ① p15 (2024 only) · ② p15 (2024; segments 생명보험/장기손해보험 inside the table) | ① p18 (2025, 2024) · ② p19-20 (2025, 2024; 2024 block restated into one merged 합계) |
| KR1107 퍼시픽 | no PDF (manifest `skipped_prior_col`, not posted) | ① p16 (2024, 2023) · ② p16 (2024, 2023) | ① p25 body (+ p186 audit-report copy, same numbers) (2025, 2024) · ② p25-34 (2025 p25-29, 2024 p30-34; 39 portfolio groups, most all-zero/dash) |
| KR1108 마이브라운 | no PDF (company licensed 2025-06; manifest `not_posted`) | no PDF (same) | ①② absent: p18 `4-6-4) 최적가정: 해당사항 없음` (text layer + **rendered 90dpi and read**: `png/kr1108_p18b.png`); p18 note 「2025년 6월 보험업 본인가 취득으로 당기(2025년)만 작성」 |
| KR1011 IBK연금 (added by coordinator) | absent | p21 `①②` company states 「연금보험 단종 보험사로 위험보험료를 포함하지 않아 … 산출하지 않음」 | p23 same sentence |

Absent is not missing: every absent cell above has a page/phrase or a keyword-0 census with a 100% text-layer reading of the document; no scan-only document was involved (all reinsurer PDFs are text-layer; text pages / total pages in the csv).

## 2. What was loaded (additions only, HEAD key diff)
Script `scripts/load_reinsurer_loss_ratio_20261012.py --apply` (log `run_load_log.txt`, proof `head_keydiff.txt`). Backup before apply: `backup_before/` (copy of HEAD; the three large files were deleted afterwards because they are byte-identical to `git show HEAD:`).

| file | HEAD -> now | HEAD rows = exact prefix | added / removed / changed keys |
|---|---|---|---|
| `risk_premium_vs_expected_claims.json` (table ② long rows) | 157,873 -> 167,025 | yes | +9,152 / 0 / 0 |
| `claims_ae_ratio.json` (table ①) | 136 -> 162 | yes | +26 / 0 / 0 (37 -> 44 companies) |
| `master_loss_ratio.json` / `.csv` | 36,344 -> 38,248 | yes | +1,904 / 0 / 0 (KR1101~KR1107: 2023.4Q 304 rows, 2024.4Q 512, 2025.4Q 1,088) |
| `census.csv` | 659 -> 738 lines | yes | +79 (KR1011's 10 census rows already existed) |
| `period_adoption.csv` / `master_census.csv` / `portfolio_taxonomy.csv` | +18 / +24 / +19 lines | yes | new codes / new labels only |
| `source_errata.csv` | 5 -> 7 lines | yes | +2 (KR1106, see 5) |
| `panel_loss_ratio.json` | unchanged | - | publishing rebuilds it |

Existing 37 companies untouched: the extended builder reproduces the committed master exactly for existing codes (`identical to committed master: True`), `build_loss_ratio_master.py --verify-only` passes (source JSON <-> master JSON <-> CSV 1:1, key dup 0, loss ratio recompute 0 mismatch).
Builder change (additive, no effect on existing rows): `scripts/build_loss_ratio_master.py` — new standard portfolio category `복합`, new 상품구분 prefixes `생명`/`장기` (see 4), sort-order lists extended.
Full rebuild of the old files was NOT used; rows were appended as text (existing bytes kept).

## 3. How the reinsurer tables were read
- Generic extractor (`extract_loss_ratio.py`, unchanged) result used where its own checks passed: KR1103 (both filings), KR1104 (both), KR1105 (both), KR1106 FY2025, KR1107 FY2024.
- New ruled-grid reader `scripts/extract_loss_ratio_reinsurer_grid_20261012.py`: the reinsurer tables are fully ruled grids with digits wrapped across lines (`1,3|51`), vertical labels, rows cut by page breaks, split year captions. Cell boxes come from the table borders; a cell = all words whose centre is inside, concatenated. Used for KR1101 (both filings), KR1102 (both), KR1107 FY2025. KR1106 FY2024 p15 (year caption not read by the generic reader) via the extractor page parse with the year forced to the printed `<2024년>` caption and segments from the heading order (`scripts/build_reinsurer_loss_ratio_rows_20261012.py`).
- Cross-validation of the two engines on the same block: KR1107 `<2024>` printed in FY2024 (generic) and FY2025 (grid): 192 common cells, 0 differences.
- Table ① rows come from the generic extractor (26 rows, all identity ok). KR1107 FY2025 `source page` set to the body page 25 (the extractor had picked the audit-report copy p186; values identical).

## 4. Label mapping (`reinsurer_label_mapping.csv`, 59 rows; raw label -> 구분/상품구분/포트폴리오)
Reinsurer labels follow the existing 구분(합계/Non-Par/Direct-Par/Indirect-Par) x (상품구분 + 포트폴리오) rule with these additions:
- `생명사망/생명건강/생명복합` (KR1101, KR1103) and `장기복합/장기질병` -> 상품구분 = the printed prefix `생명`/`장기`, 포트폴리오 = 사망/건강/복합/질병. The prefix is a 보험종목 split, not 유/무배당; it is kept as printed (no inference), and it keeps `생명복합` and `장기복합` distinct.
- `무배당복합` (KR1105, KR1106 장기손해보험) -> new standard portfolio `복합`.
- KR1102 / KR1106-FY2024 have an extra axis printed as a heading inside the table: `[생명보험]`/`[손해보험]` (KR1102) and `생명보험`/`장기손해보험` (KR1106) -> master 세그먼트 (same mechanism as 코리안리).
- KR1107 prints `유배당기타` twice in the same 구분: second occurrence relabelled `무배당기타` with flag `라벨보정` (same rule the master already applies to KR0003/KR0009/KR0029).
- `기타` without prefix (KR1104) stays 상품구분 blank (existing rule).

## 5. Identity checks (per block: 비율 ≈ A÷B within printed rounding; 합계 = Σ포트폴리오)
All 25 loaded blocks (`final_block_checks.txt`): ratio 1,760/1,783 pass; sum 926/926 pass. The 23 ratio mismatches:
- KR1107 FY2025 `<2025>`: 23 cells. The whole block prints amounts rounded to 10억원 (every value ends in 0; e.g. 합계 1년 A 2,270 / B 2,510, ratio printed 91 vs 90.44). With the 10억 rounding the ratios agree (checked in the grid reader); the master builder knows only the printed digits, so these cells carry `비율검산불일치` and the block census is `FILLED_CHECK_FLAGS` with this reason written in the census.
- KR1106 FY2025 `<2024>` 무배당질병/무배당기타 현재가치 비율 printed 84% / 86% while A÷B = 96.95% / 93.66%; both amounts close the 합계 = Σ (130,263 / 138,666). Rendered p20 at 130dpi and read the print (`png/kr1106_2025_p20.png`) -> printing error in the ratio only. Registered in `source_errata.csv` (+2 rows) and carried as `원문오기:비율` (value kept as printed), census FILLED.

## 6. Conflicts between filings (latest filing's prior-year column adopted, owner rule 2026-10-09; builder does it)
- KR1104 `<2024>`: genuine restatement of the 기타 portfolio between FY2024 and FY2025 (20 amount cells differ, max 69.85억원; ratio up to 17pp) -> 2024.4Q = FY2025 prior column, flag `RESTATED`, verdict 「진짜 정정」. Table ① 2024 also differs (FY2024 81.6/79.5/2.1 vs FY2025 97.6/91.3/6.3); both rows kept in `claims_ae_ratio.json` (2024.4Q/2024 and 2025.4Q/2024), the later one is the latest.
- KR1106 `<2024>`: FY2024 prints it segmented (생명보험 + 장기손해보험, 6 portfolios); FY2025 reprints the prior year merged into one 합계 (130,263 = 생명 + 장기손해 sums) with 3 portfolios. Cells are not comparable one to one, so the builder marks `RESTATED ... 추출확인필요` (all differences are one-sided nulls); the 2024.4Q master rows are the FY2025 merged block (rule). The segmented FY2024 block stays in the long file `risk_premium_vs_expected_claims.json` as evidence (not adopted).
- KR1103 FY2024 prints in 백만원 (decimals), FY2025 in 억원 (integers): 124 cells differ by rounding only (< 0.5); KR1102 FY2024 prints integer %, FY2025 two-decimals %: 111 ratio cells only, amounts identical; KR1101 / KR1105 / KR1107: 0 differences.

## 7. Gaps that are real absences (not missing)
2023.4Q: no reinsurer filing prints tables ①② in the FY2023_Q4 filing; the 2023.4Q column exists only as the prior-year block of the FY2024 filing: loaded for KR1103, KR1104, KR1105, KR1107 (table ②). Not available: KR1101 (FY2024 prints only `<2024년>`), KR1102 and KR1106 (FY2024 prints one block, 2024), KR1107 FY2023 PDF not posted, KR1108 not yet licensed.
Table ① 2023 column (FY2024 filing): printed by KR1101, KR1103, KR1104, KR1105, KR1107 only; the existing claims file has no 2023.4Q quarter (2024.4Q/2023 is stored as the prior-year column of the 2024.4Q filing, which is what was added) — no `2023.4Q` rows were created.

## 8. 유지율 (판매채널별, 7-8 불완전판매비율·청약철회비율 및 유지율 현황) — read only, nothing loaded
`persistency_scan.txt` / `persistency_scan2.txt` (page + phrase). All reinsurer filings state 해당사항 없음 for the whole 7-8 section:
KR1101 p58 (2023.4Q) / p61 (2024.4Q) / p69 (2025.4Q): `7.8 … 현황 – 해당사항없음`; KR1102 p47 / p56 / p60; KR1103 p23 / p29 / p29; KR1104 p24 / p53 / p53; KR1105 p55 / p66 / p65; KR1106 p45 / p44 / p61; KR1107 p38 (2024.4Q) / p86 (2025.4Q); KR1108 p55 (2025.4Q). So `data/persistency/` needs no reinsurer rows; designer may show 「해당 없음(재보험)」 instead of 「공시 없음」 for persistency (all 8 companies, every annual filing read).

## 9. Remaining / hand-offs
- publishing: rebuild `panel_loss_ratio.json` (companies keys now lack KR1101~KR1107; master and claims files have them) and sync xlsx `손해율` sheet; the HTML section 8 reads the panel.
- designer: persistency 「해당 없음(재보험)」 wording (8 above); loss-ratio panel shows the segmented labels `생명보험/손해보험`, 상품구분 `생명/장기`, portfolio `복합` for reinsurers.
- owner (flags only, nothing registered): KR1107 FY2025 10억원-rounded block flags (23 ratio cells); KR1106 2024.4Q structure change; whether `생명`/`장기` as 상품구분 is acceptable (alternative: segment axis).
- Existing taxonomy rows (40) would list reinsurer codes in 회사목록 if regenerated; not edited (additions only) — the full reinsurer mapping is in `reinsurer_label_mapping.csv`.

## 10. Reproduce
```
PY=C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
$PY scripts/extract_loss_ratio_reinsurers_20261012.py            # generic extractor on KR1101-1108 + KR1011 -> ext_A/ext_B/ext_census (derived folder only)
$PY scripts/build_reinsurer_loss_ratio_rows_20261012.py          # grid reader + KR1106 forced year -> reinsurer_B_rows.json
$PY scripts/load_reinsurer_loss_ratio_20261012.py                # dry run: additions-only proof, nothing written to data/loss_ratio
$PY scripts/load_reinsurer_loss_ratio_20261012.py --apply        # backup + append (already done; rerun only after restoring HEAD copies)
$PY data/_derived/reinsurer_loss_ratio_20261012/head_keydiff.py  # HEAD vs working tree
$PY scripts/build_loss_ratio_master.py --verify-only
```
